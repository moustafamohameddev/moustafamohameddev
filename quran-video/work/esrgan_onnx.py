"""Build an ONNX graph of Real-ESRGAN SRVGGNetCompact (realesr-general-x4v3) from the .pth
weights without PyTorch, optionally blending with the -wdn (denoise) weights like Real-ESRGAN's
--denoise_strength (dni).  Usage: esrgan_onnx.py general.pth wdn.pth strength out.onnx
"""
import pickle, sys, zipfile, collections
import numpy as np
import onnx
from onnx import helper, TensorProto, numpy_helper


def load_pth(path):
    z = zipfile.ZipFile(path)
    prefix = z.namelist()[0].split("/")[0]

    class Storage:
        def __init__(self, dtype): self.dtype = dtype

    def rebuild(storage, offset, size, stride, *args):
        arr = storage
        return np.lib.stride_tricks.as_strided(arr[offset:], shape=tuple(size),
                                               strides=tuple(s * arr.itemsize for s in stride)).copy()

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if mod == "torch._utils" and name == "_rebuild_tensor_v2":
                return rebuild
            if mod == "torch" and name.endswith("Storage"):
                return {"FloatStorage": np.float32, "HalfStorage": np.float16,
                        "LongStorage": np.int64}.get(name, np.float32)
            if mod == "collections" and name == "OrderedDict":
                return collections.OrderedDict
            return super().find_class(mod, name)

        def persistent_load(self, pid):
            _, dtype, key, _loc, _numel = pid
            return np.frombuffer(z.read(f"{prefix}/data/{key}"), dtype=dtype)

    obj = U(z.open(f"{prefix}/data.pkl")).load()
    for k in ("params_ema", "params"):
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return obj


def build(params, out_path):
    keys = sorted({int(k.split(".")[1]) for k in params}, key=int)
    nodes, inits = [], []
    x = "input"
    i = 0
    convs = [k for k in keys if params[f"body.{k}.weight"].ndim == 4]
    last = convs[-1]
    for k in keys:
        w = params[f"body.{k}.weight"].astype(np.float32)
        if w.ndim == 4:
            b = params[f"body.{k}.bias"].astype(np.float32)
            inits += [numpy_helper.from_array(w, f"w{k}"), numpy_helper.from_array(b, f"b{k}")]
            y = f"t{k}"
            nodes.append(helper.make_node("Conv", [x, f"w{k}", f"b{k}"], [y], kernel_shape=[3, 3], pads=[1, 1, 1, 1]))
        else:  # PReLU, weight shape [C]
            inits.append(numpy_helper.from_array(w.reshape(-1, 1, 1), f"s{k}"))
            y = f"t{k}"
            nodes.append(helper.make_node("PRelu", [x, f"s{k}"], [y]))
        x = y
    nodes.append(helper.make_node("DepthToSpace", [x], ["sr"], blocksize=4, mode="CRD"))
    inits.append(numpy_helper.from_array(np.array([1, 1, 4, 4], np.float32), "scales"))
    nodes.append(helper.make_node("Resize", ["input", "", "scales"], ["base"], mode="nearest"))
    nodes.append(helper.make_node("Add", ["sr", "base"], ["sum"]))
    nodes.append(helper.make_node("Clip", ["sum", "lo", "hi"], ["output"]))
    inits += [numpy_helper.from_array(np.array(0, np.float32), "lo"), numpy_helper.from_array(np.array(1, np.float32), "hi")]
    g = helper.make_graph(nodes, "srvgg",
                          [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, "h", "w"])],
                          [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, "H", "W"])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)], ir_version=9)
    onnx.checker.check_model(m)
    onnx.save(m, out_path)


if __name__ == "__main__":
    gen, wdn, strength, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    a, b = load_pth(gen), load_pth(wdn)
    p = {k: strength * a[k] + (1 - strength) * b[k] for k in a}
    build(p, out)
    print("saved", out, "layers", len(p) // 2)

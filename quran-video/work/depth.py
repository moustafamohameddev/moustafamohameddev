"""Depth maps for the scenes (Depth Anything V2 small, ONNX).
Usage (from quran-video/): python3 work/depth.py depth_anything_v2_vits.onnx
Model: https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx
"""
import sys, numpy as np, onnxruntime as ort, cv2
sess = ort.InferenceSession(sys.argv[1], providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0]; print(inp.name, inp.shape)
for i in range(1,5):
    img = cv2.imread(f"scenes/s{i}.png")[:,:,::-1].astype(np.float32)/255.
    H,W = img.shape[:2]
    h,w = 518, 518
    x = cv2.resize(img,(w,h),interpolation=cv2.INTER_CUBIC)
    x = (x-np.array([0.485,0.456,0.406]))/np.array([0.229,0.224,0.225])
    x = x.transpose(2,0,1)[None].astype(np.float32)
    d = sess.run(None,{inp.name:x})[0].squeeze()
    d = cv2.resize(d,(W,H),interpolation=cv2.INTER_CUBIC)
    d = (d-d.min())/(d.max()-d.min())   # disparity: 1 = near
    np.save(f"scenes/d{i}.npy", d.astype(np.float32))
    cv2.imwrite(f"scenes/d{i}.png",(d*255).astype(np.uint8))
    print(i, d.shape, float(d.mean()))

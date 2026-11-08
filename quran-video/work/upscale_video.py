"""Slow the 144p source to the needed length (motion-interpolated), x4 Real-ESRGAN, write 1024x576 mp4."""
import subprocess, sys, time, numpy as np, onnxruntime as ort
model, src, out, factor, dur = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
W0, H0, FPS = 256, 144, 30
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
dec = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", src, "-vf",
    f"setpts=PTS*{factor},minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
    "-t", f"{dur:.3f}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W0*4}x{H0*4}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "12",
    "-pix_fmt", "yuv444p", out], stdin=subprocess.PIPE)
n, t0 = 0, time.time()
while True:
    raw = dec.stdout.read(W0 * H0 * 3)
    if len(raw) < W0 * H0 * 3:
        break
    x = np.frombuffer(raw, np.uint8).reshape(H0, W0, 3).astype(np.float32).transpose(2, 0, 1)[None] / 255
    y = sess.run(None, {"input": x})[0][0].transpose(1, 2, 0)
    enc.stdin.write((y * 255 + 0.5).clip(0, 255).astype(np.uint8).tobytes())
    n += 1
    if n % 150 == 0:
        print(f"{n} frames, {(time.time()-t0)/n:.2f}s/frame", flush=True)
enc.stdin.close(); enc.wait(); dec.wait()
print("done", n, "frames", out, flush=True)

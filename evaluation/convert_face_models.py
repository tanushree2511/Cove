"""Export the candidate face-recognition models to ONNX (run ONCE inside a conversion venv that has torch+timm and
tensorflow+tf2onnx+deepface; the app and the evaluation only need onnxruntime).

  edgeface_s_gamma_05, edgeface_xs_gamma_06   (Idiap, torch.hub otroshi/edgeface)   input RGB, (x/255-0.5)/0.5
  ghostfacenet_w1.3_s1                        (HamadYA release v1.2, Keras h5)       input RGB, (x-127.5)/128
All take one aligned 112x112 face and return a 512-D embedding. Output: models/face_candidates/<name>.onnx
"""
import os
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "models", "face_candidates")
os.makedirs(OUT, exist_ok=True)


def edgeface_net(name):
    """EdgeFace architecture, re-implemented from the official backbones/ (Anjith George, Idiap 2023):
    a timm EdgeNeXt with a 512-D head, every non-head Linear layer replaced by a low-rank pair (rank = ratio*min dim)."""
    import timm
    import torch.nn as nn

    class LoRaLin(nn.Module):
        def __init__(self, i, o, r, bias):
            super().__init__()
            self.linear1 = nn.Linear(i, r, bias=False)
            self.linear2 = nn.Linear(r, o, bias=bias)

        def forward(self, x):
            return self.linear2(self.linear1(x))

    def lowrank(mod, ratio):
        for n, c in mod.named_children():
            if isinstance(c, nn.Linear) and "head" not in n:
                setattr(mod, n, LoRaLin(c.in_features, c.out_features, max(2, int(min(c.in_features, c.out_features) * ratio)), c.bias is not None))
            else:
                lowrank(c, ratio)

    class Wrap(nn.Module):
        def __init__(self, arch):
            super().__init__()
            self.model = timm.create_model(arch)
            self.model.reset_classifier(512)

        def forward(self, x):
            return self.model(x)

    arch, ratio = {"edgeface_s_gamma_05": ("edgenext_small", 0.5), "edgeface_xs_gamma_06": ("edgenext_x_small", 0.6)}[name]
    m = Wrap(arch)
    lowrank(m, ratio)
    return m


def edgeface(name):
    import torch
    ckpt = os.environ["EDGEFACE_CKPT"]                       # folder with the released checkpoints (edgeface repo checkpoints/)
    m = edgeface_net(name)
    m.load_state_dict(torch.load(os.path.join(ckpt, f"{name}.pt"), map_location="cpu", weights_only=True))
    m.eval()
    x = torch.randn(1, 3, 112, 112)
    torch.onnx.export(m, x, os.path.join(OUT, f"{name}.onnx"), input_names=["input"], output_names=["embedding"],
                      dynamic_axes={"input": {0: "n"}, "embedding": {0: "n"}}, opset_version=17, dynamo=False)
    print("exported", name, flush=True)


def ghostfacenet():
    import tensorflow as tf
    import tf2onnx
    from deepface.models.facial_recognition.GhostFaceNet import GhostFaceNetClient
    m = GhostFaceNetClient().model
    spec = (tf.TensorSpec((None, 112, 112, 3), tf.float32, name="input"),)
    tf2onnx.convert.from_keras(m, input_signature=spec, opset=17, output_path=os.path.join(OUT, "ghostfacenet_w1.3_s1.onnx"))
    print("exported ghostfacenet", flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or ["edge", "ghost"]
    if "edge" in which:
        for n in ("edgeface_s_gamma_05", "edgeface_xs_gamma_06"):
            edgeface(n)
    if "ghost" in which:
        ghostfacenet()

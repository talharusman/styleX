"""
Model download helper.

What the backend actually needs:
  * MediaPipe Face Mesh  - weights ship inside the `mediapipe` pip package (no download).
  * torchvision ResNet   - weights are downloaded automatically on first use.
  * OpenAI CLIP ViT-B/32 - optional (USE_CLIP=true). Requires the `clip` package:
        pip install git+https://github.com/openai/CLIP.git
    This script pre-fetches the weights so the first request is not slow.

Virtual try-on models are NOT downloaded: that module is not implemented.
"""
import sys


def main() -> int:
    try:
        import clip  # type: ignore
    except ImportError:
        print("`clip` is not installed. Install it with:\n"
              "  pip install git+https://github.com/openai/CLIP.git\n"
              "or set USE_CLIP=false (colour/rule-based fallbacks are used).")
        return 1
    print("Downloading CLIP ViT-B/32 ...")
    clip.load("ViT-B/32", device="cpu")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

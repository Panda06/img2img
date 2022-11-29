import torch
from clip_interrogator import Config, Interrogator
from diffusers import StableDiffusionPipeline, StableDiffusionOnnxPipeline


class Image2ImageModel:
    def __init__(self, clip_model_name, diffuser_model_name):

        def dummy(images, **kwargs):
            return images, False
        # Half precision is not available on cpu
        if torch.cuda.is_available():
            device = 'cuda:0'
            self.diffuser = StableDiffusionPipeline.from_pretrained(diffuser_model_name,
                                                                    torch_dtype=torch.float16)
            self.diffuser.to(device)
        else:
            device = 'cpu'
            self.diffuser = StableDiffusionOnnxPipeline.from_pretrained(diffuser_model_name,
                                                                        revision="onnx",
                                                                        provider="CUDAExecutionProvider")

        self.ci = Interrogator(Config(clip_model_name=clip_model_name, device=device))

        self.diffuser.safety_checker = dummy

    def get_prompt(self, target_image):
        return self.ci.interrogate_fast(target_image)

    def get_image(self, prompt):
        return self.diffuser(prompt, height=512, width=512).images[0]


class Model:
    model = None

    def __new__(cls):
        if Model.model is None:
            cls.model = Image2ImageModel("ViT-L/14", "CompVis/stable-diffusion-v1-4")
        return cls.model

import asyncio
import base64
import os
import shutil
from typing import Optional

import aiohttp
import gradio as gr
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from pydantic import BaseModel

from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from modules import paths, shared, devices, sd_models
import modules.script_callbacks as script_callbacks
from extensions.sd_dreambooth_extension.dreambooth import conversion, dreambooth
from webui import wrap_gradio_gpu_call

class DreamboothParameters(BaseModel):
    db_half_model: Optional[bool] = False,
    db_use_concepts: Optional[bool] = False,
    db_pretrained_model_name_or_path: str
    db_pretrained_vae_name_or_path: Optional[str] = ""
    db_instance_data_dir: str
    db_class_data_dir: Optional[str] = ""
    db_instance_prompt: Optional[str] = ""
    db_class_prompt: Optional[str] = ""
    db_file_prompt_contents: str = "Description"
    db_instance_token: str = ""
    db_class_token: str = ""
    db_save_sample_prompt: Optional[str] = ""
    db_save_sample_negative_prompt: Optional[str] = ""
    db_n_save_sample: Optional[int] = 500
    db_sample_seed: Optional[int] = -1
    db_save_guidance_scale: Optional[float] = 7.5
    db_save_infer_steps: Optional[int] = 40
    db_num_class_images: Optional[int] = 0
    db_resolution: Optional[int] = 512
    db_center_crop: Optional[bool] = False
    db_train_text_encoder: Optional[bool] = True
    db_train_batch_size: Optional[int] = 1
    db_sample_batch_size: Optional[int] = 1
    db_num_train_epochs: Optional[int] = 1
    db_max_train_steps: Optional[int] = 1000
    db_gradient_accumulation_steps: Optional[int] = 1
    db_gradient_checkpointing: Optional[bool] = True
    db_learning_rate: Optional[float] = 0.000005
    db_scale_lr: Optional[bool] = False
    db_lr_scheduler: Optional[str] = "constant"
    db_lr_warmup_steps: Optional[int] = 0
    db_attention: Optional[str] = "default"
    db_use_8bit_adam: Optional[bool] = False
    db_adam_beta1: Optional[float] = 0.9
    db_adam_beta2: Optional[float] = 0.999
    db_adam_weight_decay: Optional[float] = 0.01
    db_adam_epsilon: Optional[float] = 0.00000001
    db_max_grad_norm: Optional[int] = 1
    db_save_preview_every: Optional[int] = 500
    db_save_embedding_every: Optional[int] = 500
    db_mixed_precision: Optional[str] = "no"
    db_not_cache_latents: Optional[bool] = True
    db_concepts_list: Optional[str] = ""
    db_use_cpu: Optional[bool] = False
    db_pad_tokens: Optional[bool] = True
    db_max_token_length: Optional[int] = 75
    db_hflip: Optional[bool] = True
    db_use_ema: Optional[bool] = False
    db_class_negative_prompt: Optional[str] = ""
    db_class_guidance_scale: Optional[float] = 7.5
    db_class_infer_steps: Optional[int] = 60
    db_shuffle_after_epoch: Optional[bool] = False
    callback_url: Optional[str] = ""


def dreamBoothAPI(demo: gr.Blocks, app: FastAPI):

    #Endpoints
    @app.post("/dreambooth/createModel")
    async def createModel(
                name,
                source,
                scheduler,
                model_url,
                hub_token):
        print("Creating new Checkpoint: " + name)
        fn = conversion.extract_checkpoint(name, source, scheduler, model_url, hub_token)



    @app.post("/dreambooth/start_straining")
    async def start_training(params: DreamboothParameters, background_tasks: BackgroundTasks):
        print("Starting Training")
        train_model(params)
        return {"training": "completed"}


    #Upload Training Images base64 and save them to a folder
    @app.post("/dreambooth/upload_training_images")
    async def upload_training_images(folder: str,images: list):

        try:
            path = os.path.join(shared.cmd_opts.dreambooth_models_path,folder,"training")
        except:
            path = os.path.join(shared.models_dir,folder,"training")



        if not os.path.exists(path):
            os.makedirs(path)
        # Save images to folder
        for i, image in enumerate(images):
            with open(os.path.join(path, str(i) + ".png"), "wb") as f:
                f.write(base64.b64decode(image))
        return {"upload": "completed"}

    #Download Trained Model
    @app.get("/dreambooth/download_model/{model_name}")
    async def download_model(model_name: str):

        model_path = os.path.join("models", "Stable-diffusion", model_name +".ckpt")
        print("Downloading Model " + model_path)
        return FileResponse(model_path)


    @app.post("/dreambooth/upload_model")
    async def upload_model(model_name: str, model: UploadFile = File(...)):
        print("Uploading Model")
        with open(os.path.join("models", "Stable-diffusion", model_name +".ckpt"), "wb") as buffer:
            shutil.copyfileobj(model.file, buffer)
        return {"upload": "completed"}



    #Async Trainings
    async def train_model(params: DreamboothParameters):
        print("Training Model")
        fn = wrap_gradio_gpu_call(dreambooth.start_training(
            params.db_pretrained_model_name_or_path,
            params.db_half_model,
            params.db_use_concepts,
            params.db_pretrained_vae_name_or_path,
            params.db_instance_data_dir,
            params.db_class_data_dir,
            params.db_instance_prompt,
            params.db_class_prompt,
            params.db_file_prompt_contents,
            params.db_instance_token,
            params.db_class_token,
            params.db_save_sample_prompt,
            params.db_save_sample_negative_prompt,
            params.db_n_save_sample,
            params.db_sample_seed,
            params.db_save_guidance_scale,
            params.db_save_infer_steps,
            params.db_num_class_images,
            params.db_resolution,
            params.db_center_crop,
            params.db_train_text_encoder,
            params.db_train_batch_size,
            params.db_sample_batch_size,
            params.db_num_train_epochs,
            params.db_max_train_steps,
            params.db_gradient_accumulation_steps,
            params.db_gradient_checkpointing,
            params.db_learning_rate,
            params.db_scale_lr,
            params.db_lr_scheduler,
            params.db_lr_warmup_steps,
            params.db_attention,
            params.db_use_8bit_adam,
            params.db_adam_beta1,
            params.db_adam_beta2,
            params.db_adam_weight_decay,
            params.db_adam_epsilon,
            params.db_max_grad_norm,
            params.db_save_preview_every,
            params.db_save_embedding_every,
            params.db_mixed_precision,
            params.db_not_cache_latents,
            params.db_concepts_list,
            params.db_use_cpu,
            params.db_pad_tokens,
            params.db_max_token_length,
            params.db_hflip,
            params.db_use_ema,
            params.db_class_negative_prompt,
            params.db_class_guidance_scale,
            params.db_class_infer_steps,
            params.db_shuffle_after_epoch
        ))
        async with aiohttp.ClientSession() as session:
            async with session.get(params.callback_url) as resp:
                print(resp.status)
                print(await resp.text())




script_callbacks.on_app_started(dreamBoothAPI)

print("Dreambooth API layer loaded")

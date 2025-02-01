import random
import glob
import numpy as np
import torch
import os
import sys
import re
import json
import hashlib
import comfy.sd
import folder_paths
import requests 
import piexif
import time
import secrets

from safetensors import safe_open
from collections import deque
from datetime import datetime
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from PIL import ExifTags
from typing import Dict

class AnyType(str):
  def __ne__(self, __value: object) -> bool:
    return False

any = AnyType("*")

def get_sha256(self, file_path: str):
    file_no_ext = os.path.splitext(file_path)[0]
    hash_file = file_no_ext + ".sha256"

    if os.path.exists(hash_file):
        try:
            with open(hash_file, "r") as f:
                return f.read().strip()
        except OSError as e:
            print(f"Error reading existing hash file: {e}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    try:
        with open(hash_file, "w") as f:
            f.write(sha256_hash.hexdigest())
    except OSError as e:
        print(f"Error writing hash to {hash_file}: {e}")

    return sha256_hash.hexdigest()

def generate_unique_seed():
    return time.time_ns() ^ secrets.randbits(64)
    #return time.time_ns()

################################

class SimpleLoadLineFromTextFile:     

    def __init__(self):
        self.batch_counter = 0
        self.line_counter = 0
        self.random_list = []
        self.my_random = random.Random() #isolated generator

    @classmethod
    def IS_CHANGED(s, **kwargs):
        #always update
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):  
        #input_dir = folder_paths.get_input_directory()
        #files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {   
                "name": ("STRING", {"default": "", "multiline": False, "tooltip": "Node name"}), 
                "start": ("INT", {"default": 0, "min": 0, "step": 1, "tooltip": "Start position for increment or decrement methods"}),
                "load_file": ("BOOLEAN", {"default": True, "tooltip": "if True, load center of prompt from file"}),
                "file_path": ("STRING", {"default": "", "multiline": False, "tooltip": "Path to the file from which the lines for the central part of the prompt will be taken"}),
                "next": (["increment", "decrement", "random", "random no repetitions"], {"default":"increment", "tooltip": "Option for enumerating lines, in case of randomness the start parameter is ignored"}),      
            },
            "optional": {
                "prefix": ("STRING", {"multiline": True, "default": "", "tooltip": "Add text to the beginning of the prompt"}),   
                "postfix": ("STRING", {"multiline": True, "default": "", "tooltip": "Add text to the ending of the prompt"}),
                "count": ("INT", {"default": 0, "min": 0, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING","INT","INT","INT")
    RETURN_NAMES = ("text","batch_counter","line_counter","lines")
    FUNCTION = "read_text_file"
    CATEGORY = "📚 SimpleButcher"
    DESCRIPTION = "Simple prompt loader from a text file to automate the batch process. Can be combined with each other and create total randomness text and lora that is taken from your text and lora templates"

    def read_text_file(self, name = "", start = 0, load_file = False, file_path = "", next = "increment", prefix = "", postfix = "", count = 0):

        if count == 0:
            self.batch_counter = 0
            self.line_counter = start
            print(f"\033[93mClear counter\033[0m")

        self.batch_counter = self.batch_counter + 1

        lines2 = []      
        line_count = 0  

        if file_path != "":
          if load_file == True:
            file_path = os.path.expandvars(file_path)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"The file at path '{file_path}' does not exist.")
            with open(file_path, 'r', encoding='ISO-8859-1') as file: #utf-8
                lines = file.readlines()
            
            for line in lines:
                line = line.replace("\r","")
                line = line.strip()
                if line != "":
                    lines2.append(line)

            line_count = len(lines2)

        text = ""
        if prefix != "":
            text = prefix + " "  

        current_line = 0
        if line_count > 0:

            if next == "random no repetitions":
                if count == 0:
                    # save random numbers
                    random_seed = generate_unique_seed()
                    #print(f"\033[93m{random_seed}\033[0m")
                    self.my_random.seed(random_seed)
                    self.random_list = list(range(0, line_count))
                    self.my_random.shuffle(self.random_list)
                rnd = self.batch_counter % len(self.random_list)
                self.line_counter = self.random_list[rnd]
            elif next == "random":
                if count == 0:
                    # randomize
                    random_seed = generate_unique_seed()
                    #print(f"\033[93m{random_seed}\033[0m")
                    self.my_random.seed(random_seed)
                rnd = self.my_random.randint(0, line_count-1)
                self.line_counter = rnd

            self.line_counter = self.line_counter % line_count
            text = text + lines2[self.line_counter]
            current_line = self.line_counter

            console_text = f"[\033[95mBatch {name}: {self.batch_counter}\033[0m -> \033[92mLine: {str(current_line)}/{str(line_count)}\033[0m]"
            print(f"{console_text}")

            if next == "increment":
                self.line_counter = self.line_counter+1
            elif next == "decrement":
                self.line_counter = self.line_counter-1
                if self.line_counter < 0:
                    self.line_counter = line_count-1
        else:
            console_text = f"[\033[95mBatch {name}: {self.batch_counter}\033[0m -> Skip"
            print(f"{console_text}")
                    
        if postfix != "":
            text = text + " " + postfix

        text = text.replace("\r","")
        text = text.replace("\n"," ")
        text = text.replace("<"," <")
        
        return (text,self.batch_counter,current_line,line_count)

################################

class SimpleExtractLoraFromText:     

    @classmethod
    def INPUT_TYPES(cls):
               
        return {"required": {       
                    "text": ("STRING", {"multiline": True, "default": "", "tooltip": "Text with mixed lora and prompt", "forceInput": True}),
                    }
                }

    RETURN_TYPES = ("STRING","STRING")
    RETURN_NAMES = ("lora_text","prompt")
    FUNCTION = "extract_lora"
    CATEGORY = "📚 SimpleButcher"
    DESCRIPTION = "If the text contains lore, written in Forge style: <lora:name:1.0> or <lora:name:unet=1.0:te=0.75>, this node splits the text into prompts and lore separately"

    def extract_lora(self, text):

        text_prompt = text

        text_loras = re.findall(r'<lora:[^>]*>', text)
        text_lora = ' '.join(text_loras)
        text_lora = text_lora.strip()

        #text_prompt = ' '.join(s for s in text.split() if not (s.startswith("<") and s.endswith(">")))
        #text_prompt = ' '.join(word for word in text.split() if not re.search('<.*?>', word)) 
        text_prompt = re.sub('<.*?>', '', text)       

        text_prompt = text_prompt.replace(",,",",")
        text_prompt = text_prompt.replace(" ,",",")
        text_prompt = text_prompt.replace(",",", ")
        text_prompt = text_prompt.replace("  "," ")
        text_prompt = text_prompt.strip()
        text_prompt = text_prompt.strip(",")
        text_prompt = text_prompt.strip()

        return (text_lora,text_prompt)            

################################

class SimpleLoraLoader:   
  
    def __init__(self):
        self.loaded_lora = []
        self.cache_size = 0

    @classmethod
    def INPUT_TYPES(cls):  
        return {"required": {   
                    "model": ("MODEL", {"tooltip": "The diffusion model the LoRA will be applied to"}),  
                    "clip": ("CLIP", {"tooltip": "The CLIP model the LoRA will be applied to"}),
                    "lora_text": ("STRING", {"multiline": False, "default": "", "tooltip": "Multiple LoRAs discriptions in Forge style: <lora:name:1.0> or <lora:name:unet=1.0:te=0.75>", "forceInput": True}),
                    },
                "optional": {
                    "multiple_strength_unet": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05, "tooltip": "Multiple of unet strength"}),
                    "multiple_strength_clip": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05, "tooltip": "Multiple of clip strength"}),
                    "limit_strength_unet": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.05, "tooltip": "Max of unet strength"}),
                    "limit_strength_clip": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.05, "tooltip": "Max of clip strength"}),
                    "count": ("INT", {"default": 1, "min": 0, "step": 1}),
                    }
                }

    RETURN_TYPES = ("MODEL","CLIP","STRING","STRING")
    RETURN_NAMES = ("model","clip","civitai_lora","civitai_lora_hash")
    FUNCTION = "lora_loader"
    CATEGORY = "📚 SimpleButcher"
    DESCRIPTION = "Multiple LoRAs loader, understands discriptions in Forge style: <lora:name:1.0> or <lora:name:unet=1.0:te=0.75>. Understands both file names and internal lore names (Forge style). Once creates a lora_name.json dictionary and places it in the lora folder to speed up. Once creates a lora templates to __txt folder. In case of lora update just delete these files and press F5 in confy-ui."

    def load_lora_name(self, path_list):

        json_path = os.path.join(path_list[0],"lora_name.json")

        name_lines = []
        json_lines = []

        for directory in path_list:
          console_text = f"[\033[94mFind LoRA File in {directory}\033[0m]"
          print(f"{console_text}")
          for root, dirs, files in os.walk(directory):
            for file in files:
              if file.endswith(".safetensors"):
                full_filepath = os.path.join(root, file)
                filepath = full_filepath.replace(directory+"\\", "")
                lora_name1 = os.path.splitext(file)[0]
                lora_name2 = "None"
                with safe_open(full_filepath, framework="pt", device="cpu") as f:
                    if f.metadata() != None:
                        if "ss_output_name" in f.metadata():
                            lora_name2 = f.metadata()["ss_output_name"]
                            if lora_name2 == "lora":
                                lora_name2 = "None"
                            if lora_name2 == "":
                                lora_name2 = "None"
                        #elif "modelspec.title" in f.metadata():
                        #    lora_name2 = f.metadata()["modelspec.title"]
              
                hash_value_10_chars = get_sha256(self,full_filepath)[:10]    

                subdirectory = os.path.dirname(filepath)
                if subdirectory == "":
                  subdirectory = "root"
                subdirectory = subdirectory.replace("\\","_")

                if lora_name2 == "None":
                    console_text = f"[\033[95m{hash_value_10_chars}\033[0m] {filepath} -> \033[91m{lora_name2}\033[0m"
                    name_lines.append([subdirectory,"<lora:"+lora_name1+":1.0>"])
                else:
                    console_text = f"[\033[95m{hash_value_10_chars}\033[0m] {filepath} -> \033[92m{lora_name2}\033[0m"
                    name_lines.append([subdirectory,"<lora:"+lora_name2+":1.0>"])
                print(f"{console_text}")

                json_lines.append([filepath,lora_name1,lora_name2,hash_value_10_chars])

          console_text = f"[\033[94mEnd\033[0m]"
          print(f"{console_text}")

        with open(json_path, 'w') as file:
            json.dump(json_lines, file)      

#        txt_path = path_list[0] + "\\__txt"
#        if not os.path.exists(txt_path):
#            os.makedirs(txt_path, exist_ok=True)

#        data_dict = {}
#        for name, value in name_lines:
#          if name not in data_dict:
#            data_dict[name] = []  
#          data_dict[name].append(value)

#        for name, values in data_dict.items():
#          with open(txt_path+f"\\Lora in {name}.txt", "w", encoding="utf-8") as file:
#            for value in values:
#              file.write(f"{value}\n")  

        return ()  


    def lora_loader(self, model, clip, lora_text, multiple_strength_unet = 1.0, multiple_strength_clip = 1.0, limit_strength_unet = 2.0, limit_strength_clip = 2.0, count = 1):

        if count == 0:
            print(f"\033[93mClick clear button\033[0m")

        lora_path_list = folder_paths.get_folder_paths("loras")

        json_path = os.path.join(lora_path_list[0],"lora_name.json")

        if (not os.path.isfile(json_path)) or (count == 0):
            print(f"\033[93mLoad dictionary\033[0m")
            self.load_lora_name(lora_path_list)
            
        dic = []
        if os.path.isfile(json_path):
            with open(json_path, 'r') as file:
                data = json.load(file)
                dic = [tuple(item) for item in data]

        loras = re.findall(r'<lora:[^>]*>', lora_text)

        civitai_lora = ""
        civitai_lora_hash = ""

        #print(f"Cache size = {len(self.loaded_lora)}")

        for item in self.loaded_lora:
            item[2] = False

        unique_elements = set()

        for lora in loras:
            lora = lora.replace("<lora:","")
            lora = lora.replace(">","")
            parts = lora.split(":", 1)
            lora_prompt_name = parts[0]
            lora_path = ""
            lora_hash = ""

            #find by filename
            for item in dic: 
                if item[1] == lora_prompt_name:
                    lora_path = item[0]
                    lora_hash = item[3]
                    break

            #or find by internal lora name
            if lora_path == "":
                for item in dic: 
                    if item[2] == lora_prompt_name:
                        lora_path = item[0]
                        lora_hash = item[3]
                        break

            #not found
            if lora_path == "":
                console_text = f"[\033[91m-Lora: {lora_prompt_name}\033[0m] not found"
                print(f"{console_text}")
                continue

            #skip duplicate
            if lora_path in unique_elements:
               console_text = f"[\033[91m-Lora: {lora_path}\033[0m] skip duplicate"
               print(f"{console_text}")
               continue

            unique_elements.add(lora_path) 

##########################
##### parce strength #####

            strength_model = 1.0
            strength_clip = 1.0  

            if len(parts) == 2:
                lora_parameter = parts[1]
                parts = lora_parameter.split(":")
                if len(parts) == 1:
                    try:
                        strength_model = float(lora_parameter)
                        strength_model = round(strength_model, 2)
                    except:
                       strength_model = 1.0
                    strength_clip = strength_model
                else:   
                    for part in parts:
                        parts2 = part.split("=")
                        if parts2[0] == "unet":
                            try:
                                strength_model = float(parts2[1])
                                strength_model = round(strength_model, 2)
                            except:
                                strength_model = 1.0
                        elif parts2[0] == "te":
                            try:
                                strength_clip = float(parts2[1])
                                strength_clip = round(strength_clip, 2)
                            except:
                                strength_clip = 1.0

            if multiple_strength_unet != 1.0:
                strength_model = round(strength_model * multiple_strength_unet, 2)

            if multiple_strength_clip != 1.0:
                strength_clip = round(strength_clip * multiple_strength_clip, 2)

            if strength_model > limit_strength_unet:
                strength_model = limit_strength_unet

            if strength_clip > limit_strength_clip:
                strength_clip = limit_strength_clip

##### parce strength #####
##########################

            strength_model_str = "{:.2f}".format(strength_model)
            strength_clip_str = "{:.2f}".format(strength_clip)   

            if strength_model == strength_clip:
                civitai_lora = civitai_lora + "<lora:" + lora_prompt_name + ":" + strength_model_str + "> "
            else:
                civitai_lora = civitai_lora + "<lora:" + lora_prompt_name + ":unet=" + strength_model_str + ":te=" + strength_clip_str + "> "
                
            civitai_lora_hash = civitai_lora_hash + lora_prompt_name + ": " + lora_hash + ", "          
      
            lora = None
            postfix = ""
            for item in self.loaded_lora:
                if item[0] == lora_path:
                    lora = item[1]
                    item[2] = True
                    postfix = " cache"
            if lora == None:
                full_path = folder_paths.get_full_path_or_raise("loras", lora_path)   
                lora = comfy.utils.load_torch_file(full_path, safe_load=True)
                self.loaded_lora.append([lora_path,lora,True])
                postfix = " load"
            model,clip = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
            
            if strength_model == strength_clip:
                console_text = f"[\033[94m+Lora: {lora_path}:\033[92m{strength_model_str}\033[0m]{postfix}"
                print(f"{console_text}")
            else:
                console_text = f"[\033[94m+Lora: {lora_path}:\033[92m{strength_model_str}:{strength_clip_str}\033[0m]{postfix}"
                print(f"{console_text}")

##### Empty catch #####
        for i in range(len(self.loaded_lora)-1, -1, -1): #reverse order
            if not self.loaded_lora[i][2]: 
              temp = self.loaded_lora[i][1] 
              del self.loaded_lora[i]
              del temp    

        civitai_lora_hash = civitai_lora_hash.rstrip(", ")
        civitai_lora = civitai_lora.strip()

        return (model,clip,civitai_lora,civitai_lora_hash)  


################################

class SimpleImageSaver:  
   
    @classmethod
    def INPUT_TYPES(cls):  
        return {
            "required": {
                    "images": ("IMAGE", { "tooltip": "image(s) to save", "forceInput": True}),
                    "prompt": ("STRING", {"default": "", "multiline": False, "tooltip": "STRING", "forceInput": True}),
                    "output_path": ("STRING", {"default": "", "multiline": False, "tooltip": "Path where images will be saved"}),
                    "SEED": ("INT",  {"default": '0', "tooltip": "INT", "forceInput": True}),
                    "modelname": ("STRING",  {"default": '', "multiline": False, "tooltip": "STRING, use Checkpoint Loader with Name (Image Saver) node", "forceInput": True}),
            },
            "optional": {
                    "steps": ("INT", {"default": 0, "tooltip": "INT", "forceInput": True}),
                    "sampler": (any, {"default": None, "tooltip": "ANY, use Sampler Selector (Image Saver) node", "forceInput": True}),
                    "schedule": (any, {"default": None, "tooltip": "ANY, use Scheduler Selector (Image Saver) node", "forceInput": True}),
                    "CFG_scale": ("FLOAT", {"default": 0.0, "tooltip": "FLOAT", "forceInput": True}),
                    "distilled_CFG_scale": ("FLOAT", {"default": 0.0, "tooltip": "FLOAT", "forceInput": True}),
                    "width": ("INT", {"default": 0, "tooltip": "INT", "forceInput": True}),
                    "height": ("INT", {"default": 0, "tooltip": "INT", "forceInput": True}),
                    "beta_schedule_alpha": ("FLOAT", {"default": 0.0, "tooltip": "FLOAT", "forceInput": True}),
                    "beta_schedule_beta": ("FLOAT", {"default": 0.0, "tooltip": "FLOAT", "forceInput": True}),
                    "civitai_lora": ("STRING",  {"default": '', "multiline": False, "tooltip": "STRING, Loras name from Simple Lora Loader node", "forceInput": True}),
                    "civitai_lora_hash": ("STRING",  {"default": '', "multiline": False, "tooltip": "STRING, Loras hash from Simple Lora Loader node", "forceInput": True}),
                    "negative": ("STRING",  {"default": '', "multiline": False, "tooltip": "STRING, Negative prompt", "forceInput": True}),
                    "save_workflow": ("BOOLEAN", {"default": False, "tooltip": "if True, saves workflow in the image"}),  
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("metadata_text",)
    FUNCTION = "image_saver"
    CATEGORY = "📚 SimpleButcher"
    DESCRIPTION = "SimpleImageSaver"
    OUTPUT_NODE = True
    DESCRIPTION = "Image Saver with metadata in Forge style. Loras name and hash could be obtained from Simple Lora Loader node. Сreated subfolders with date, output files contain a sequence number and seed, as Forge does."

    def find_free_number(self, path):
        i = -1
        for filename in os.listdir(path):
            if os.path.isfile(os.path.join(path, filename)):
                new = -1
                try:
                    new = int(filename[:5])
                except:
                    new = -1
                if new > i:
                    i = new
        return i+1

    def image_saver(self, images, prompt, output_path, SEED, modelname, steps=0, sampler=None, schedule=None, CFG_scale=0.0, distilled_CFG_scale=0.0, width=0, height=0, beta_schedule_alpha=0.0, beta_schedule_beta=0.0, civitai_lora="", civitai_lora_hash="",negative="",save_workflow=False,extra_pnginfo=None):

        metadata_text = ""

        now = datetime.now()
        date = now.strftime("%Y-%m-%d")

        output_path = output_path.strip()
        if output_path == '':
            return ()

        output_path = os.path.join(output_path, date)

        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            free_number = self.find_free_number(output_path)
            if free_number > 99999:
                print(f"\033[91mToo many files\033[0m")
                return ()

            seed_text = str(SEED)

####################
##### metadata #####

            prompt_and_lora = prompt
            if civitai_lora != "":
                prompt_and_lora = prompt_and_lora + ' ' + civitai_lora

            metadata_text = prompt_and_lora + '\n' 

            if negative != "":
                metadata_text = metadata_text + "Negative prompt: "+ negative + '\n'

            if steps != 0:
                metadata_text = metadata_text + "Steps: "+str(steps)+", "
            if sampler != None:
                metadata_text = metadata_text + "Sampler: "+str(sampler)+", "
            if schedule != None:
                metadata_text = metadata_text + "Schedule type: "+str(schedule)+", "
            if CFG_scale != 0.0:
                metadata_text = metadata_text + "CFG scale: "+str(CFG_scale)+", "
            if distilled_CFG_scale != 0.0:
                metadata_text = metadata_text + "Distilled CFG Scale: "+str(distilled_CFG_scale)+", "
            metadata_text = metadata_text + "Seed: "+seed_text+", "
            if width != 0:
                if height != 0:
                    metadata_text = metadata_text + "Size: " + str(width) + "x" + str(height) + ", "

            ckpt_path = folder_paths.get_full_path("checkpoints", modelname)
            if not ckpt_path:
                ckpt_path = folder_paths.get_full_path("diffusion_models", modelname)
            if ckpt_path:
                modelhash = get_sha256(self,ckpt_path)[:10]
            else:
                modelhash = ""
            if modelhash != "":
                metadata_text = metadata_text + "Model hash: "+modelhash+", "
            modelname = os.path.basename(modelname)
            modelname = os.path.splitext(modelname)[0]
            if modelname != "":
                metadata_text = metadata_text + "Model: "+modelname+", "
            
            if beta_schedule_alpha != 0.0:
                metadata_text = metadata_text + "Beta schedule alpha: "+str(beta_schedule_alpha)+", "
            if beta_schedule_beta != 0.0:
                metadata_text = metadata_text + "Beta schedule beta: "+str(beta_schedule_beta)+", "

            if civitai_lora_hash != "":
                metadata_text = metadata_text + "Lora hashes: \"" + civitai_lora_hash + "\", "

            metadata_text = metadata_text + "Version: ComfyUI"

            metadata = PngInfo()
            metadata.add_text("parameters", metadata_text)

            if save_workflow:
                if prompt_and_lora != "":
                    metadata.add_text("prompt", prompt_and_lora)
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        print(f"Write {x}")
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            
##### metadata #####
####################

            filename = f"{free_number:05d}-{seed_text}.png"
            img.save(os.path.join(output_path, filename), pnginfo=metadata, optimize=False)

        return (metadata_text,)  


################################

class SimpleLoadImageWithMetadataString:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {"required":
                    {"image": (sorted(files), )},
                }
    CATEGORY = "📚 SimpleButcher"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata_forge", "prompt")
    FUNCTION = "read_image"
    DESCRIPTION = "Load Image with metadata in simple string!"

    def read_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        i = Image.open(image_path)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
        width = i.width
        height = i.height
        format = i.format
        metadata = i.info

        #exif_workflow = ""
        #if "workflow" in metadata:
        #  exif_workflow = metadata["workflow"]

        exif_prompt = ""
        if "prompt" in metadata:
          exif_prompt = metadata["prompt"]
        
        exif_metadata = ""
        if "parameters" in metadata:
          exif_metadata = metadata["parameters"]

        return (image, mask, exif_metadata, exif_prompt)

    @classmethod
    def IS_CHANGED(s, image):
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True

################################

NODE_CLASS_MAPPINGS = { 
    "Simple Load Line From Text File": SimpleLoadLineFromTextFile,
    "Simple Extract Lora From Text": SimpleExtractLoraFromText,
    "Simple Lora Loader": SimpleLoraLoader,
    "Simple Image Saver (as Forge)": SimpleImageSaver,
    "Simple Load Image With Metadata": SimpleLoadImageWithMetadataString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Simple Load Line From Text File": "Simple Load Line From Text File 📚",
    "Simple Extract Lora From Text": "Simple Extract Lora From Text 📚",
    "Simple Lora Loader": "Simple Lora Loader 📚",
    "Simple Image Saver (as Forge)": "Simple Image Saver (as Forge) 📚",
    "Simple Load Image With Metadata": "Simple Load Image With Metadata 📚",
}


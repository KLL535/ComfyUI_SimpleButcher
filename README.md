# ComfyUI_SimpleButcher

### Why is this needed:
I needed to automate the process of generating images and I did not find ready-made simple solutions for this, so I wrote my own. 
The idea is to repeat the functionality of forge: the script "Prompts from file or textbox". 
So that you can easily sort through pre-prepared lists of prompts, lora, styles, and connect text as you like.
The resulting images must be compatible with Forge, and ideally, no different from it. 
The problem is that Forge uses the internal name from the Lora file metadata as the lora name, not the file name. 
Therefore, all existing solutions simply did not understand my templates. 
I would also like it if lore could be written in any order and any quantity in a text file in this format: `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>` and this would be applied automatically, without the need to create nodes for each lora separately.
I would like the `civitai` site to understand metadata, the closest to this was the `alexopus/ComfyUI-Image-Saver` project, but it loses lora written in Forge style, by internal name.

![workflow](https://github.com/user-attachments/assets/9014a2a0-c507-4872-b5eb-9a29b3b87518)
[!] You need to remove the first node with empty text, so that it does not block the execution of the chain, since the text in it does not change.

## How to install?

### Method 1: Manager (Recommended)
If you have *ComfyUI-Manager*, you can click `Install via Git URL` and install these custom nodes `https://github.com/KLL535/ComfyUI_SimpleButcher.git`.

### Method 2: Manual
In Windows:
- run `cmd`, go to the ComfyUI folder
- `cd custom_nodes`
- `git clone https://github.com/KLL535/ComfyUI_SimpleButcher.git`
- `cd ComfyUI_SimpleButcher`
- `.\..\..\..\python_embeded\python.exe -s -m pip install -r requirements.txt`
- Start/restart ComfyUI

## Node: Simple Load Line From Text File
Simple prompt loader from a text file to automate the batch process. 
Can be combined with each other and create total randomness text and lora that is taken from your text and lora templates.

#### Input:
- `start` - *INT* - Start position for increment or decrement methods.
- `load_file` - *BOOLEAN* - if True, load center of prompt from file.
- `file_path` - *STRING* - Path to the file from which the lines for the central part of the prompt will be taken.
- `next` - `increment` or `decrement` or `random` or `random no repetitions` - Option for enumerating lines, in case of randomness the start parameter is ignored. In the latter case, the lines will be selected randomly, but without repetitions.  
- `prefix` - *STRING* - Add text to the beginning of the prompt (optional).
- `postfix` - *STRING* - Add text to the ending of the prompt (optional).
#### Output:
- `text` - *STRING* - Output text based on the principle: `prefix` + `line from file` + `postfix`.
- `batch_counter` - *INT* - Current batch counter, if you start a new batch the counter will reset to 1.
- `line_counter` - *INT* - Current line counter from file.
- `lines` - *INT* - Total lines in file. If batch is greater than lines in file, they will be read in a loop.

![a](https://github.com/user-attachments/assets/0c785b8a-85a3-4863-a04f-fc6f3869a392)

## Node: Simple Extract Lora From Text
If the text contains lore, written in Forge style: `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`, this node splits the text into prompts and lore separately

#### Input:
- `text` - *STRING* - Text with mixed lora and prompt.
#### Output:
- `lora_text` - *STRING* - The text contains only lora
- `prompt` - *STRING* - The text contains only prompt

![b](https://github.com/user-attachments/assets/fc1b65a2-acde-4e72-ab3a-05c09ffb2d06)

## Node: Simple Lora Loader
Multiple LoRAs loader, understands discriptions in Forge style: <lora:name:1.0> or <lora:name:unet=1.0:te=0.75>. 
Understands both file names and internal lore names (Forge style). 
Once creates a `lora_name.json` dictionary and places it in the lora folder to speed up. 
Once creates a lora templates to `__txt` folder. 
Additionally, the hash of all lora is read once.
In case of lora update just delete these files and press F5 in confy-ui.

#### Input:
- `model` - *MODEL* - The diffusion model the LoRA will be applied to.  
- `clip` - *CLIP* - The CLIP model the LoRA will be applied to.
- `lora_text` - *STRING* - Multiple LoRAs discriptions in Forge style: `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`
- `multiple_strength_unet` - *FLOAT* - Multiple of unet strength. If there is a lot of lore, they can spoil the model, it is possible to multiply the weight of all incoming lore by this coefficient.
- `multiple_strength_clip` - *FLOAT* - Multiple of clip strength. 
- `limit_strength_unet` - *FLOAT* - Max of unet strength. If there are a lot of lore, they can spoil the model, it is possible to limit the weight of all incoming lore to this number.
- `limit_strength_clip` - *FLOAT* - Max of clip strength. 
#### Output:
- `model` - *MODEL* - Output diffusion model.  
- `clip` - *CLIP* -  Output CLIP model.
- `civitai_lora` - *STRING* - List of loras and their weights that were applied to the model.
- `civitai_lora_hash` - *STRING* - The first 10 characters of the hash sum of the loras, needed for the civitai of the site.
  
![c](https://github.com/user-attachments/assets/03116a8a-d5c2-4d50-9956-b655bd9e7d3f)

## Node: Simple Image Saver (as Forge)
Image Saver with metadata in Forge style. Loras name and hash could be obtained from Simple Lora Loader node. Сreated subfolders with date. Output files contain a sequence number and seed, as Forge does.

#### Input:
- `images` - *IMAGE* - image(s) to save.
- `prompt` - *STRING*. 
- `output_path` - *STRING* - Path where images will be saved.
- `SEED` - *INT*.
- `modelname` - *STRING* - Use `Checkpoint Loader with Name (Image Saver)` node.
##### Optional metadata (as Forge).
If not connected these lines will be missing:
- `steps` - *INT*. 
- `sampler` - *any* -  use `Sampler Selector (Image Saver)` node.
- `schedule` - *any* - use `Scheduler Selector (Image Saver)` node.
- `CFG_scale` - *FLOAT*. 
- `distilled_CFG_scal` - *FLOAT*.
- `width` - *INT*.
- `height` - *INT*.
- `beta_schedule_alph` - *FLOAT*.
- `beta_schedule_beta` - *FLOAT*.
- `civitai_lora` - *STRING* - Loras name from Simple Lora Loader node.
- `civitai_lora_hash` - *STRING* - Loras hash from Simple Lora Loader node.
- `negative` - *STRING*.
#### Output:
- `metadata_text` - *STRING* - Metadata written to file.

![d](https://github.com/user-attachments/assets/e767e065-5e99-4718-bc80-e169ecc9f471)

## Info in terminal
3 node `Simple Load Line From Text File` running:

![image](https://github.com/user-attachments/assets/e9eb3980-6454-4682-90cf-a37452a1200b)

Maybe it will be useful to someone. This is my first project, there may be mistakes.

[!] Tested on Windows only. Tested on Flux only.

[!] The code from following resources were used:
https://github.com/Suzie1/ComfyUI_Guide_To_Making_Custom_Nodes
https://github.com/alexopus/ComfyUI-Image-Saver
https://github.com/AonekoSS/ComfyUI-SimpleCounter

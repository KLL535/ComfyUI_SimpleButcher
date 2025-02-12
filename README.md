# ComfyUI_SimpleButcher

### Description:
Node to automate batch generation with randomize prompts from text files. It mimics **Forge's** functionality, allowing you to combine text elements and LoRA. The node supports writing LoRA in any order within a text file using formats like `<lora:name:1.0>`, without needing separate nodes. The node understands LoRA names in **Forge's`** style, when the name is not the filename, but the internal name from the metadata.

### Why is this needed:
I needed to automate the process of generating images and could not find any straightforward ready-made solutions for this purpose. Hence, I developed my own solution. The primary idea is to replicate and expand **Forge's** functionality: specifically, the `Prompts from file or textbox` script. This will allow you to easily combine pre-prepared lists of prompts, LoRA, styles, allowing you to combine texts as you wish.
The resulting images prompt in metadata must be compatible with **Forge**, ideally appearing no different than those generated by it. However, I encountered a problem because **Forge** uses the internal name from the LoRA file metadata as the LoRA's name instead of the filename. Consequently, all existing solutions failed to comprehend my templates.
I also wish for the ability to write LoRA in any order and quantity within a text file using this format: `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`. This should be automatically applied without the need to create separate nodes for each LoRA. Additionally, I would like it if the **CivitAI** platform could understand metadata. As the closest solution I found was the `alexopus/ComfyUI-Image-Saver` project. However, this alternative loses LoRA written in **Forge** style by using the internal name instead of the filename.

![workflow](https://github.com/user-attachments/assets/9014a2a0-c507-4872-b5eb-9a29b3b87518)

### Caution:
[!] This nodes create a new file in LoRA/Model ditectory:
- files `*.sha256` next to LoRA, the file contains the hash sum of the LoRA file.
- files `*.sha256` next to model, the file contains the hash sum of the model file.
- file `lora_name.json` in first LoRA folder (default path `ComfyUI\models\loras\`).

## How to install?

### Method 1: Manager (Recommended)
If you have *ComfyUI-Manager*, you can click `Custom Nodes Manager` and find `ComfyUI_SimpleButcher`.

### Method 2: Manual
In Windows:
- run `cmd`, go to the ComfyUI folder
- `cd custom_nodes`
- `git clone https://github.com/KLL535/ComfyUI_SimpleButcher.git`
- `cd ComfyUI_SimpleButcher`
- `.\..\..\..\python_embeded\python.exe -s -m pip install -r requirements.txt`
- Start/restart ComfyUI

## Node 1: Simple Load Line From Text File
Simple tool for loading prompts directly from a text file, enabling automation of the entire batch process. You can combine this nodes to generate fully randomized texts and LoRA, sourced from your own text and LORA templates.

#### Input:
- `name` - *STRING* - Just a name. To avoid confusing nodes if there are many of them.
- `start` - *INT* - Start position for increment or decrement methods.
- `load_file` - *BOOLEAN* - if True, load center of prompt from file.
- `file_path` - *STRING* - Path to the file from which the lines for the central part of the prompt will be taken.
- `next` - `increment` or `decrement` or `fixed` or `random` or `random no repetitions` - Option for enumerating lines, in case of randomness the start parameter is ignored. In the latter case, the lines will be selected randomly, but without repetitions.  
- `prefix` - *STRING* - Add text to the beginning of the prompt (optional).
- `postfix` - *STRING* - Add text to the ending of the prompt (optional).
#### Output:
- `text` - *STRING* - Output text based on the principle: `prefix` + `line from file` + `postfix`.
- `batch_counter` - *INT* - Current batch counter, if you start a new batch the counter will reset to 1.
- `line_counter` - *INT* - Current line counter from file.
- `lines` - *INT* - Total lines in file. If batch is greater than lines in file, they will be read in a loop.

![image](https://github.com/user-attachments/assets/69b1c311-f706-4195-b20a-faa918a19851)

## Node 2: Simple Extract Lora From Text
If the input text includes LoRA written in `Forge` style, such as `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`, this node automatically segregates the text into separate prompts and LoRA.

#### Input:
- `text` - *STRING* - Text with mixed lora and prompt.
#### Output:
- `lora_text` - *STRING* - The text contains only lora
- `prompt` - *STRING* - The text contains only prompt

![b](https://github.com/user-attachments/assets/fc1b65a2-acde-4e72-ab3a-05c09ffb2d06)

## Node 3: Simple Lora Loader
This tool can load multiple LoRAs described in Forge style, such as `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`. It recognizes both file names and internal LoRA names obtained from the metadata of `*.safetensors` files via the `ss_output_name` field.
When the workflow is first run, a dictionary `lora_name.json` is generated to store the lora paths, internal names and hash, and is saved in the LoRA folder to speed up future operations. Hash values ​​for all LoRA are calculated once and stored in `*.sha256` files next to each LoRA. If there are many files and the hash has not been calculated before, this process may take a long time. If you update LoRAs place, add new LoRA, simply click button `Update LoRA dictionary` and run workflow, this will update the file `lora_name.json`.

#### Input:
- `model` - *MODEL* - The diffusion model the LoRA will be applied to.  
- `clip` - *CLIP* - The CLIP model the LoRA will be applied to.
- `lora_text` - *STRING* - Multiple LoRAs discriptions in Forge style: `<lora:name:1.0>` or `<lora:name:unet=1.0:te=0.75>`
- `multiple_strength_unet` - *FLOAT* - Multiple of unet strength. If there is a lot of lore, they can spoil the model, it is possible to multiply the weight of all incoming lore by this coefficient.
- `multiple_strength_clip` - *FLOAT* - Multiple of clip strength. 
- `limit_strength_unet` - *FLOAT* - Max of unet strength. If there are a lot of lore, they can spoil the model, it is possible to limit the weight of all incoming lore to this number.
- `limit_strength_clip` - *FLOAT* - Max of clip strength.
- `Update LoRA dictionary` - *Button* - Click this button and run workflow will update the file `lora_name.json` (if you update LoRAs place or add new LoRA).
#### Output:
- `model` - *MODEL* - Output diffusion model.  
- `clip` - *CLIP* -  Output CLIP model.
- `civitai_lora` - *STRING* - List of loras and their weights that were applied to the model.
- `civitai_lora_hash` - *STRING* - The first 10 characters of the hash sum of the loras, needed for the **CivitAI** site.
  
![image](https://github.com/user-attachments/assets/0cbc124e-c73d-4254-811f-1b700eee5db9)

## Node 4: Simple Image Saver (as Forge)
Image Saver designed for saved metadata in Forge-style, allowing retrieval of LoRAs' names and hashes directly from the `Simple LoRA Loader node`. This tool automatically organizes output images into subfolders based on the date. The filenames of the saved files include a sequence number and seed. Hash values ​​for current model are calculated once and stored in `*.sha256` files next to model.

#### Input:
- `images` - *IMAGE* - image(s) to save.
- `output_path` - *STRING* - Path where images will be saved.

##### Optional metadata (as Forge).
If not connected these lines will be missing:
- `prompt_text` - *STRING*. 
- `SEED` - *INT*. If the `override_parameters` input is connected, the seed will be read from there.
- `modelname` - *STRING* - Use `Checkpoint Loader with Name (Image Saver)` node.
- `steps` - *INT*. 
- `sampler` - *any* -  use `Sampler Selector (Image Saver)` node.
- `schedule` - *any* - use `Scheduler Selector (Image Saver)` node.
- `CFG_scale` - *FLOAT*. 
- `distilled_CFG_scal` - *FLOAT*.
- `width` - *INT*.
- `height` - *INT*.
- `beta_schedule_alph` - *FLOAT*.
- `beta_schedule_beta` - *FLOAT*.
- `civitai_lora` - *STRING* - Loras name from `Simple Lora Loader` node.
- `civitai_lora_hash` - *STRING* - Loras hash from `Simple Lora Loader` node.
- `negative` - *STRING* - negative prompt if needed.
- `override_parameters` - *STRING* - replaces all above parameters, if they have already been collected. 
- `override_workflow` - *STRING* - replaces the current workflow. `Json` text.
- `override_prompt` - *STRING* - replaces the current prompt data. `Json` text.
- `save_comfy_workflow` - *BOOLEAN* - if **True**, saves the current workflow to metadata.
- `save_comfy_prompt` - *BOOLEAN* - if **True**, saves the current prompt data (not `prompt_text`) to metadata.
#### Output:
- `metadata_text` - *STRING* - Metadata written to file.

## Node 5: Simple Load Image With Metadata
This node is made to upload images with all metadata, including **Forge's** metadata, so as not to lose them.
As far as I understand, there are three metadata fields:
- `parameters` - A convenient representation. It is easy to open the image metadata and read the prompt.
- `workflow` - The workflow is stored here, so that later it can be loaded by dragging the file, in principle, it is convenient. But it is very difficult for a person to read this.
- `prompt` - I do not understand what is stored here. It is very difficult for a person to read this. 

#### Output:
- `image` -  *IMAGE* - load image
- `mask` - *MASK* - mask of image
- `metadata_parameters (forge)` - *STRING* - metadata **Forge**.
- `metadata_workflow` - *STRING* - workflow **Comfy-ui**. `Json` text.
- `metadata_prompt` - *STRING* - metadata **Comfy-ui**. `Json` text.

A simple way to re-save an image without losing metadata.
If you connect a workflow, you can save the previous workflow.
If you do not connect a workflow, the current workflow will be saved.

![image](https://github.com/user-attachments/assets/dfe71a81-d7c3-4b6f-a6a5-7ec2cc8ff251)

## Node 6: Simple Load Images from Dir
Same as for text, only for batch images from a directory.

 #### Advantages over other solutions:
- Supports non-repetition random mode (to go through all images without repetitions, but randomly, the batch count should be equal than the number of images).
- Supports output of raw metadata (including Forge metadata) to avoid losing it.

 #### Input:
- `name` - *STRING* - Just a name. To avoid confusing nodes if there are many of them.
- `input_path` - *STRING* - Path to the dir to images.
- `start` - *INT* - Start position for increment or decrement methods.
- `next` - `increment` or `decrement` or `fixed` or `random` or `random no repetitions` - Option for enumerating files, in case of randomness the start parameter is ignored. In the latter case, the files will be selected randomly, but without repetitions.  
- `include_subdir` - *BOOLEAN* - Turn on to read all images and subdirectories too.

#### Output:
- `image` -  *IMAGE* - load image
- `mask` - *MASK* - mask of image
- `metadata_parameters (forge)` - *STRING* - metadata **Forge**.
- `metadata_workflow` - *STRING* - workflow **Comfy-ui**. `Json` text.
- `metadata_prompt` - *STRING* - metadata **Comfy-ui**. `Json` text.
- `batch_counter` - *INT* - Current batch counter, if you start a new batch the counter will reset to 1.
- `line_counter` - *INT* - Current file counter.
- `lines` - *INT* - Total files. If batch is greater than files, they will be open in a loop.

![image](https://github.com/user-attachments/assets/728bd697-1948-493d-87e9-15efd7c657eb)

## Info in terminal
3 node `Simple Load Line From Text File` running:

![image](https://github.com/user-attachments/assets/e9eb3980-6454-4682-90cf-a37452a1200b)

Maybe it will be useful to someone. 

[!] Tested on Windows only. Tested on Flux and SDXL.

[!] The code from following resources were used:
- https://github.com/Suzie1/ComfyUI_Guide_To_Making_Custom_Nodes
- https://github.com/alexopus/ComfyUI-Image-Saver
- https://github.com/AonekoSS/ComfyUI-SimpleCounter

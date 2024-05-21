import os
from collections import defaultdict
from PIL import Image, ExifTags
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
import send2trash
from tqdm import tqdm

def load_label2image_paths(base_path):
    label2image_paths = defaultdict(list)

    def recurse(current_path, current_label):
        for entry in os.listdir(current_path):
            entry_path = os.path.join(current_path, entry)
            if os.path.isdir(entry_path):
                new_label = current_label + [entry]
                recurse(entry_path, new_label)
            elif entry.lower().endswith('.jpg'):
                label = '_'.join(current_label)
                label2image_paths[label].append(entry_path)

    recurse(base_path, [])
    print("=============================labels===================================")
    print("\n".join(label2image_paths.keys()))
    print("=============================labels===================================")
    return label2image_paths

def correct_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

def crop_image(image, crop_size, offset):
    width, height = image.size
    new_width, new_height = crop_size
    left = (width - new_width) / 2 + offset[0]
    top = (height - new_height) / 2 + offset[1]
    right = (width + new_width) / 2 + offset[0]
    bottom = (height + new_height) / 2 + offset[1]
    return image.crop((left, top, right, bottom))

def load_images(image_paths):
    images = []
    for image_path in image_paths:
        image = Image.open(image_path)
        image = correct_orientation(image)
        images.append(image)
    return images

def load_label2images(label2image_paths):
    label2images = defaultdict(list)
    for label, image_paths in label2image_paths.items():
        label2images[label] = load_images(image_paths)
    return label2images       

def process_images(image_paths, crop_params, compress_size): # crop and compress
    images = load_images(image_paths)
    processed_images = []
    for image in images:
        cropped_image = crop_image(image, crop_params['size'], crop_params['offset'])
        resized_image = cropped_image.resize(compress_size)
        processed_images.append(resized_image)
    return processed_images

def adjust_and_create_mosaic(crop_dict, compress_size, label2image_paths):
    def create_mosaic(processed_images, compress_size, original_paths):
        num_images = len(processed_images)
        cols = int(num_images**0.5)
        rows = (num_images + cols - 1) // cols

        mosaic_width = cols * compress_size[0]
        mosaic_height = rows * compress_size[1]
        mosaic = Image.new('RGB', (mosaic_width, mosaic_height))

        for i, (image, path) in enumerate(zip(processed_images, original_paths)):
            mosaic.paste(image, (compress_size[0] * (i % cols), compress_size[1] * (i // cols)))

        return mosaic, cols, rows
    
    def update_mosaic():
        global fig, cols, rows, files_to_delete
        if fig:
            plt.close(fig)
            
        # delete file
        for f in files_to_delete:
            send2trash.send2trash(f)
            
        indices_to_delete = [i for i, element in enumerate(files) if element in files_to_delete]
        for index in sorted(indices_to_delete, reverse=True):
            del files[index]
            
        files_to_delete = []
        
        crop_size = (int(size_var.get()), int(size_var.get()))
        offset = (int(offset_x_var.get()), int(offset_y_var.get()))
        crop_params = {'size': crop_size, 'offset': offset}
        processed_images = process_images(files, crop_params, compress_size)
        mosaic, cols, rows = create_mosaic(processed_images, compress_size, files)
        fig = plt.figure(figsize=(10, 10))
        plt.imshow(mosaic)
        plt.title(f'Label: {current_label}')
        plt.axis('off')
        fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()
        
    def next_label():
        global current_label_index, current_label, files, fig
        if fig:
            plt.close(fig)

        # 输出当前 label 的 size 和 offset
        current_crop_size = (int(size_var.get()), int(size_var.get()))
        current_offset = (int(offset_x_var.get()), int(offset_y_var.get()))
        print(f'"{current_label}": {{"size": {current_crop_size}, "offset": {current_offset}}}, ')

        current_label_index += 1
        if current_label_index >= len(labels):
            current_label_index = 0
        current_label = labels[current_label_index]
        files = label2image_paths[current_label]
        crop_size = crop_dict[current_label]['size']
        size_var.set(crop_size[0])
        offset_x_var.set(crop_dict[current_label].get('offset', (0, 0))[0])
        offset_y_var.set(crop_dict[current_label].get('offset', (0, 0))[1])
        update_mosaic()

        
    def on_click(event):
        global files_to_delete
        if event.inaxes is not None and event.button == MouseButton.LEFT:
            col = int(event.xdata // compress_size[0])
            row = int(event.ydata // compress_size[1])
            index = row * cols + col
            if index < len(files):
                if messagebox.askyesno("Confirm Delete", f"Do you really want to delete {files[index]}?") and files[index] not in files_to_delete:
                    files_to_delete.append(files[index])

    global size_var, offset_x_var, offset_y_var, files, current_label, current_label_index, labels, fig, cols, rows, files_to_delete
    
    files_to_delete = []
    labels = [label for label in crop_dict if label in label2image_paths]
    current_label_index = 0
    current_label = labels[current_label_index]
    files = label2image_paths[current_label]

    root = Tk()
    root.title("Offset and Size Adjustment")
    root.geometry("400x300")

    size_label = Label(root, text="Size")
    size_label.pack()
    size_var = StringVar()
    size_entry = Entry(root, textvariable=size_var)
    size_entry.pack()

    offset_x_label = Label(root, text="Offset X")
    offset_x_label.pack()
    offset_x_var = StringVar()
    offset_x_entry = Entry(root, textvariable=offset_x_var)
    offset_x_entry.pack()

    offset_y_label = Label(root, text="Offset Y")
    offset_y_label.pack()
    offset_y_var = StringVar()
    offset_y_entry = Entry(root, textvariable=offset_y_var)
    offset_y_entry.pack()

    update_button = Button(root, text="Update Mosaic", command=update_mosaic)
    update_button.pack()

    next_button = Button(root, text="Next Label", command=next_label)
    next_button.pack()

    crop_size = crop_dict[current_label]['size']
    size_var.set(crop_size[0])
    offset_x_var.set(crop_dict[current_label].get('offset', (0, 0))[0])
    offset_y_var.set(crop_dict[current_label].get('offset', (0, 0))[1])
    update_mosaic()

    root.mainloop()

def save_processed_images(label2image_paths, crop_dict, compress_size):
    for label, params in tqdm(crop_dict.items()):
        if label in label2image_paths:
            files = label2image_paths[label]
            crop_size = params['size']
            crop_params = {'size': crop_size, 'offset': params.get('offset', (0, 0))}
            processed_images = process_images(files, crop_params, compress_size)
            save_dir = os.path.join('./processed', *label.split('_'))
            os.makedirs(save_dir, exist_ok=True)
            for i, image in enumerate(processed_images):
                image.save(os.path.join(save_dir, f"{i+1}.jpg"))

def main():
    global fig, compress_size, cols, rows
    compress_size = (64, 64)
    fig = None
    
    crop_dict = {
        "FamilyMart_morning_5m_left_30deg": {"size": (700, 700), "offset": (50, -300)}, 
        "FamilyMart_morning_5m_left_60deg": {"size": (600, 600), "offset": (50, 0)}, 
        "FamilyMart_morning_5m_right_30deg": {"size": (600, 600), "offset": (60, -225)},
        "FamilyMart_morning_5m_right_60deg": {"size": (600, 600), "offset": (0, 0)}, 
        "FamilyMart_morning_5m_0deg": {"size": (700, 700), "offset": (0, -400)}, 
        "FamilyMart_morning_7.5m_0deg": {"size": (600, 600), "offset": (0, -150)}, 
        "FamilyMart_morning_7.5m_left_30deg": {"size": (550, 550), "offset": (0, -125)}, 
        "FamilyMart_morning_7.5m_left_60deg": {"size": (500, 500), "offset": (0, 0)}, 
        "FamilyMart_morning_7.5m_right_30deg": {"size": (400, 400), "offset": (50, -60)}, 
        "FamilyMart_morning_7.5m_right_60deg": {"size": (500, 500), "offset": (80, 75)}, 
        "FamilyMart_morning_10m_0deg": {"size": (375, 375), "offset": (30, 25)}, 
        "FamilyMart_morning_10m_left_30deg": {"size": (500, 500), "offset": (50, -50)}, 
        "FamilyMart_morning_10m_left_60deg": {"size": (500, 500), "offset": (50, 10)},
        "FamilyMart_morning_10m_right_30deg": {"size": (625, 625), "offset": (100, -235)}, 
        "FamilyMart_morning_10m_right_60deg": {"size": (450, 450), "offset": (100, 200)}, 
        "FamilyMart_night_5m_left_30deg": {"size": (450, 450), "offset": (0, -100)},
        "FamilyMart_night_5m_left_60deg": {"size": (375, 375), "offset": (0, -150)},
        "FamilyMart_night_5m_right_30deg": {"size": (450, 450), "offset": (-100, 0)},
        "FamilyMart_night_5m_right_60deg": {"size": (375, 375), "offset": (175, 0)},
        "FamilyMart_night_5m_0deg": {"size": (450, 450), "offset": (0, -300)},#
        "FamilyMart_night_7.5m_0deg": {"size": (375, 375), "offset": (-50, -175)},
        "FamilyMart_night_7.5m_left_30deg": {"size": (300, 300), "offset": (-50, -50)},
        "FamilyMart_night_7.5m_left_60deg": {"size": (275, 275), "offset": (50, -160)},
        "FamilyMart_night_7.5m_right_30deg": {"size": (300, 300), "offset": (0, -175)},
        "FamilyMart_night_7.5m_right_60deg": {"size": (275, 275), "offset": (100, -50)},
        "FamilyMart_night_10m_0deg": {"size": (250, 250), "offset": (0, -70)},
        "FamilyMart_night_10m_left_30deg": {"offset": (-50, -100)},
        "FamilyMart_night_10m_left_60deg": {"size": (225, 225), "offset": (0, 18)},
        "FamilyMart_night_10m_right_30deg": {"size": (250, 250), "offset": (0, 50)},
        "FamilyMart_night_10m_right_60deg": {"size": (200, 200), "offset": (100, 125)},
        "Ching-Shin_morning_5m_left_30deg": {"size": (600, 600), "offset": (75, -450)}, 
        "Ching-Shin_morning_5m_left_60deg": {"size": (600, 600), "offset": (100, -175)}, 
        "Ching-Shin_morning_5m_right_30deg": {"size": (600, 600), "offset": (0, -450)}, 
        "Ching-Shin_morning_5m_right_60deg": {"size": (550, 550), "offset": (0, -525)}, 
        "Ching-Shin_morning_5m_0deg": {"size": (500, 500), "offset": (50, -250)}, 
        "Ching-Shin_morning_7.5m_0deg": {"size": (300, 300), "offset": (50, -400)},
        "Ching-Shin_morning_7.5m_left_30deg": {"size": (450, 450), "offset": (0, -400)},
        "Ching-Shin_morning_7.5m_right_30deg": {"size": (500, 500), "offset": (0, -380)}, 
        "Ching-Shin_morning_7.5m_right_60deg": {"size": (450, 450), "offset": (50, -300)}, 
        "Ching-Shin_morning_10m_0deg": {"size": (300, 300), "offset": (100, -350)}, 
        "Ching-Shin_morning_10m_left_30deg": {"size": (300, 300), "offset": (0, -300)}, 
        "Ching-Shin_morning_10m_right_30deg": {"size": (300, 300), "offset": (0, -300)}, 
        "Ching-Shin_morning_10m_right_60deg": {"size": (325, 325), "offset": (0, -180)},
        "Ching-Shin_night_5m_left_30deg": {"size": (400, 400), "offset": (0, -75)},
        "Ching-Shin_night_5m_left_60deg": {"size": (350, 350), "offset": (-150, -125)},
        "Ching-Shin_night_5m_right_30deg": {"size": (350, 350), "offset": (-75, -175)},
        "Ching-Shin_night_5m_right_60deg": {"size": (300, 300), "offset": (100, -50)},
        "Ching-Shin_night_5m_0deg": {"size": (450, 450), "offset": (0, 0)},
        "Ching-Shin_night_7.5m_0deg": {"size": (225, 225), "offset": (0, -60)},
        "Ching-Shin_night_7.5m_left_30deg": {"size": (250, 250), "offset": (50, 225)},
        "Ching-Shin_night_7.5m_right_30deg": {"size": (200, 200), "offset": (0, 50)},
        "Ching-Shin_night_7.5m_right_60deg": {"size": (200, 200), "offset": (50, -75)},
        "Ching-Shin_night_10m_0deg": {"size": (275, 275), "offset": (-25, -20)},
        "Ching-Shin_night_10m_left_30deg": {"size": (225, 225), "offset": (-90, 35)},
        "Ching-Shin_night_10m_right_30deg": {"size": (250, 250), "offset": (50, -25)},
        "Ching-Shin_night_10m_right_60deg": {"size": (275, 275), "offset": (0, -20)},
    }
    
    is_decide_crop_size_and_offset = input("Do you want to decide every label's crop size and offset? (yes/no) [default: no] : ").lower()
    is_save_preprocess_images = input("Do you want to save your preprocessed images in ./compress folder? (yes/no) [default: no] : ").lower()
    
    if is_decide_crop_size_and_offset == "yes" or is_save_preprocess_images == "yes":
        label2image_paths = load_label2image_paths('./original')
    
    if is_decide_crop_size_and_offset == "yes":
        adjust_and_create_mosaic(crop_dict, compress_size, label2image_paths)
    
    if is_save_preprocess_images == "yes":
        save_processed_images(label2image_paths, crop_dict, compress_size)

if __name__ == "__main__":
    main()

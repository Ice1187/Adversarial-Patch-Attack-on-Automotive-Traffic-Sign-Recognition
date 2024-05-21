import os
from collections import defaultdict
from PIL import Image, ExifTags

################################################# testing loaded image ########################################################
import random
import matplotlib.pyplot as plt

def show_random_images(label2images, num_images=10):
    # 存放選定的圖像及其標籤
    selected_images_with_labels = []

    # 從字典中隨機選擇圖像及其標籤
    all_labels_and_images = [(label, img) for label, imgs in label2images.items() for img in imgs]
    if len(all_labels_and_images) < num_images:
        selected_images_with_labels = all_labels_and_images
    else:
        selected_images_with_labels = random.sample(all_labels_and_images, num_images)

    # 計算每個子圖的大小
    subplot_size = int(num_images**0.5)

    # 設置畫圖布局，增加figsize
    fig, axs = plt.subplots(nrows=subplot_size, ncols=subplot_size, figsize=(20, 12))

    # 展示圖像和標籤
    for ax, (label, img) in zip(axs.ravel(), selected_images_with_labels):
        ax.imshow(img)
        ax.set_title(label, fontsize=10)  # 設置標籤，並調整字體大小和旋轉角度
        ax.axis('off')

    # 調整子圖間距和布局
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.tight_layout()
    plt.show()

################################################# testing loaded image ###################################################
    
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

label2images = load_label2images(load_label2image_paths("./processed"))
show_random_images(label2images, 50)
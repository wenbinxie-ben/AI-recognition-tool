# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Train a YOLOv5 model on a custom dataset.

Models and datasets download automatically from the latest YOLOv5 release.
Models: https://github.com/ultralytics/yolov5/tree/master/models
Datasets: https://github.com/ultralytics/yolov5/tree/master/data
Tutorial: https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data

Usage:
    $ python path/to/train.py --data coco128.yaml --weights yolov5s.pt --img 640  # from pretrained (RECOMMENDED)
    $ python path/to/train.py --data coco128.yaml --weights '' --cfg yolov5s.yaml --img 640  # from scratch
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from AI_recognition_tool import Ui_AI_recognition_tool
from PyQt5.QtCore import QThread, pyqtSignal
import sys

import os
from os import listdir, getcwd
from os.path import join
import subprocess
import random
import shutil
import re
import xml.etree.ElementTree as ET
import pickle

import argparse
import math
import os
import random
import sys
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.distributed as dist
import torch.nn as nn
import yaml
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.optim import SGD, Adam, AdamW, lr_scheduler
from tqdm import tqdm

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

import val  # for end-of-epoch mAP
from models.experimental import attempt_load
from models.yolo import Model
from utils.autoanchor import check_anchors
from utils.autobatch import check_train_batch_size
from utils.callbacks import Callbacks
from utils.dataloaders import create_dataloader
from utils.downloads import attempt_download
from utils.general import (LOGGER, check_amp, check_dataset, check_file, check_git_status, check_img_size,
                           check_requirements, check_suffix, check_version, check_yaml, colorstr, get_latest_run,
                           increment_path, init_seeds, intersect_dicts, labels_to_class_weights,
                           labels_to_image_weights, methods, one_cycle, print_args, print_mutation, strip_optimizer)
from utils.loggers import Loggers
from utils.loggers.wandb.wandb_utils import check_wandb_resume
from utils.loss import ComputeLoss
from utils.metrics import fitness
from utils.plots import plot_evolve, plot_labels
from utils.torch_utils import EarlyStopping, ModelEMA, de_parallel, select_device, torch_distributed_zero_first

import argparse
import os
import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync

from pathlib import Path

LOCAL_RANK = int(os.getenv('LOCAL_RANK', -1))  # https://pytorch.org/docs/stable/elastic/run.html
RANK = int(os.getenv('RANK', -1))
WORLD_SIZE = int(os.getenv('WORLD_SIZE', 1))




class mainwindow(QMainWindow, Ui_AI_recognition_tool):
    sin = pyqtSignal()
    def __init__(self):
        super(mainwindow, self).__init__()
        self.myThread = RunThread()
        self.sin.connect(self.myThread.stop)
        self.setupUi(self)

        self.Labelling_Button.clicked.connect(self.open_labelling)
        self.Convert_Button.clicked.connect(self.convert_dataset)
        self.Yaml_Button.clicked.connect(self.create_cfg)
        self.Train_Button.clicked.connect(lambda: self.work(self.Train_Button.text()))
        self.Stop_Train_Button.clicked.connect(lambda: self.work(self.Stop_Train_Button.text()))
        self.Detect_Button.clicked.connect(self.detect)

        sys.stdout = Signal()
        sys.stdout.text_update.connect(self.updatetext)


    def open_labelling(self):
        cwd = os.getcwd()
        # print(cwd)
        # path = 'r"' + str(cwd) + '\labelImg.exe"'
        path = str(cwd) + '\labelImg.exe'
        print(path)
        a = os.startfile(path)


    def convert_dataset(self):

        random.seed(0)

        xmlfilepath = r'./VOC2007/Annotations'
        saveBasePath = r"./VOC2007/ImageSets/Main/"

        float_trainval_percent = float(self.trainval_percent_lineEdit.text())
        float_train_percent = float(self.train_percent_lineEdit.text())
        print("float_trainval_percent = " + str(float_trainval_percent))
        print("float_train_percent = " + str(float_train_percent))

        trainval_percent = float_trainval_percent
        train_percent = float_train_percent

        temp_xml = os.listdir(xmlfilepath)
        total_xml = []
        for xml in temp_xml:
            if xml.endswith(".xml"):
                total_xml.append(xml)

        num = len(total_xml)
        list = range(num)
        tv = int(num * trainval_percent)
        tr = int(tv * train_percent)
        trainval = random.sample(list, tv)
        train = random.sample(trainval, tr)

        print("train and val size", tv)
        print("traub suze", tr)

        ftest = open(os.path.join(saveBasePath, 'test.txt'), 'w')
        ftrain = open(os.path.join(saveBasePath, 'train.txt'), 'w')
        fval = open(os.path.join(saveBasePath, 'val.txt'), 'w')

        for i in list:
            name = total_xml[i][:-4] + '\n'
            if i in trainval:
                if i in train:
                    ftrain.write(name)
                else:
                    fval.write(name)
            else:
                ftest.write(name)

        ftrain.close()
        fval.close()
        ftest.close()

        saveBasePath = "./VOC2007/ImageSets/Main/"

        with open(os.path.join(saveBasePath, 'train.txt')) as f:
            train_number = f.readlines()

        with open(os.path.join(saveBasePath, 'val.txt')) as f:
            val_number = f.readlines()

        with open(os.path.join(saveBasePath, 'test.txt')) as f:
            test_number = f.readlines()

        train_image = []
        val_image = []
        test_image = []

        for i in train_number:
            i = i.rstrip('\n')
            i_image = i + '.jpg'
            train_image.append(i_image)
        print(train_image)

        for i in val_number:
            i = i.rstrip('\n')
            i_image = i + '.jpg'
            val_image.append(i_image)
        print(val_image)

        for i in test_number:
            i = i.rstrip('\n')
            i_image = i + '.jpg'
            test_image.append(i_image)
        print(test_image)

        new_train = "./images/train/"
        if not os.path.exists('./images/train/'):
            os.makedirs('./images/train/')
        new_val = "./images/val/"
        if not os.path.exists('./images/val/'):
            os.makedirs('./images/val/')
        new_test = "./images/test/"
        if not os.path.exists('./images/test/'):
            os.makedirs('./images/test/')

        dir_path = "./VOC2007/JPEGImages/"
        for i in train_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_train)

        for i in val_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_val)

        for i in test_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_test)


        sets = ['train', 'test', 'val']

        line_edit_classes = self.class_name_lineEdit.text()
        split_classes: list[str] = re.split(',| ', line_edit_classes)
        print(split_classes)

        classes = split_classes

        def convert(size, box):
            dw = 1. / size[0]
            dh = 1. / size[1]
            x = (box[0] + box[1]) / 2.0
            y = (box[2] + box[3]) / 2.0
            w = box[1] - box[0]
            h = box[3] - box[2]
            x = x * dw
            w = w * dw
            y = y * dh
            h = h * dh
            return (x, y, w, h)

        def convert_annotation(image_id):
            in_file = open('./VOC2007/Annotations/%s.xml' % (image_id))
            out_file = open('./voc2007/labels/%s.txt' % (image_id), 'w')
            tree = ET.parse(in_file)
            root = tree.getroot()
            size = root.find('size')
            w = int(size.find('width').text)
            h = int(size.find('height').text)
            for obj in root.iter('object'):
                difficult = obj.find('difficult').text
                cls = obj.find('name').text
                if cls not in classes or int(difficult) == 1:
                    continue
                cls_id = classes.index(cls)
                xmlbox = obj.find('bndbox')
                b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text),
                     float(xmlbox.find('ymax').text))
                bb = convert((w, h), b)
                out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')

        wd = os.getcwd()
        print(wd)
        for image_set in sets:
            if not os.path.exists('./VOC2007/labels/'):
                os.makedirs('./VOC2007/labels/')
            image_ids = open('./VOC2007/ImageSets/Main/%s.txt' % (image_set)).read().strip().split()
            list_file = open('./VOC2007/%s.txt' % (image_set), 'w')
            for image_id in image_ids:
                list_file.write('./VOC2007/Images/%s.jpg\n' % (image_id))
                convert_annotation(image_id)
            list_file.close()

        saveBasePath = "./VOC2007/ImageSets/Main/"

        with open(os.path.join(saveBasePath, 'train.txt')) as f:
            train_number = f.readlines()

        with open(os.path.join(saveBasePath, 'val.txt')) as f:
            val_number = f.readlines()

        with open(os.path.join(saveBasePath, 'test.txt')) as f:
            test_number = f.readlines()

        train_image = []
        val_image = []
        test_image = []

        for i in train_number:
            i = i.rstrip('\n')
            i_image = i + '.txt'
            # print(i_image)
            train_image.append(i_image)
        print(train_image)

        for i in val_number:
            i = i.rstrip('\n')
            i_image = i + '.txt'
            # print(i_image)
            val_image.append(i_image)
        print(val_image)

        for i in test_number:
            i = i.rstrip('\n')
            i_image = i + '.txt'
            # print(i_image)
            test_image.append(i_image)
        print(test_image)

        new_train = "./labels/train/"
        if not os.path.exists('./labels/train/'):
            os.makedirs('./labels/train/')
        new_val = "./labels/val/"
        if not os.path.exists('./labels/val/'):
            os.makedirs('./labels/val/')
        new_test = "./labels/test/"
        if not os.path.exists('./labels/test/'):
            os.makedirs('./labels/test/')

        dir_path = "./VOC2007/labels/"
        for i in train_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_train)

        for i in val_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_val)

        for i in test_image:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file == i:
                        shutil.copy(os.path.join(root, file), new_test)

        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Information', 'Finish!', QMessageBox.Ok)
        msg_box.exec_()

    def create_cfg(self):
        yaml_data_name = str(self.Yaml_data_lineEdit.text())
        yaml_models_name = str(self.Yaml_models_lineEdit.text())

        cwd = str(os.getcwd())

        line_edit_classes = self.class_name_lineEdit.text()
        split_classes: list[str] = re.split(',| ', line_edit_classes)
        print(split_classes)
        classes_str = ''
        for i in range(0,len(split_classes)):
            if i == len(split_classes)-1:
                classes_str = classes_str + "'" + split_classes[i] + "'"
            else:
                classes_str = classes_str + "'" + split_classes[i] + "'" + ", "
        final_classes_str = "[" + classes_str + "]"
        print(final_classes_str)

        n_number = str(self.class_number_lineEdit.text())

        dm = str(self.dm_lineEdit.text())
        wm = str(self.wm_lineEdit.text())

        yaml_data_content = "train: " + cwd + r"\images\train" + "\n" \
                            + "val: " + cwd + r"\images\val" + "\n" \
                            + "test: " + cwd + r"\images\test" + "\n"\
                            + "\n"\
                            + "nc: " + n_number + "\n"\
                            + "\n"\
                            + "names: " + final_classes_str

        yaml_models_content = \
                            """
# YOLOv5 🚀 by Ultralytics, GPL-3.0 license

# Parameters
                            """ + "\n"\
                            + "nc: " + n_number + "\n"\
                             + "depth_multiple: " + dm + "\n"\
                            + "width_multiple: " + wm + "\n"\
                            + """
anchors:
- [10,13, 16,30, 33,23]  # P3/8
- [30,61, 62,45, 59,119]  # P4/16
- [116,90, 156,198, 373,326]  # P5/32

# YOLOv5 v6.0 backbone
backbone:
# [from, number, module, args]
[[-1, 1, Conv, [64, 6, 2, 2]],  # 0-P1/2
[-1, 1, Conv, [128, 3, 2]],  # 1-P2/4
[-1, 3, C3, [128]],
[-1, 1, Conv, [256, 3, 2]],  # 3-P3/8
[-1, 6, C3, [256]],
[-1, 1, Conv, [512, 3, 2]],  # 5-P4/16
[-1, 9, C3, [512]],
[-1, 1, Conv, [1024, 3, 2]],  # 7-P5/32
[-1, 3, C3, [1024]],
[-1, 1, SPPF, [1024, 5]],  # 9
]

# YOLOv5 v6.0 head
head:
[[-1, 1, Conv, [512, 1, 1]],
[-1, 1, nn.Upsample, [None, 2, 'nearest']],
[[-1, 6], 1, Concat, [1]],  # cat backbone P4
[-1, 3, C3, [512, False]],  # 13

[-1, 1, Conv, [256, 1, 1]],
[-1, 1, nn.Upsample, [None, 2, 'nearest']],
[[-1, 4], 1, Concat, [1]],  # cat backbone P3
[-1, 3, C3, [256, False]],  # 17 (P3/8-small)

[-1, 1, Conv, [256, 3, 2]],
[[-1, 14], 1, Concat, [1]],  # cat head P4
[-1, 3, C3, [512, False]],  # 20 (P4/16-medium)

[-1, 1, Conv, [512, 3, 2]],
[[-1, 10], 1, Concat, [1]],  # cat head P5
[-1, 3, C3, [1024, False]],  # 23 (P5/32-large)

[[17, 20, 23], 1, Detect, [nc, anchors]],  # Detect(P3, P4, P5)
]
                              """
        print(yaml_models_content)

        data_filename = "./data/" + yaml_data_name + ".yaml"
        os.makedirs(os.path.dirname(data_filename), exist_ok=True)
        with open(data_filename, "w", encoding='utf-8') as f:
            f.write(yaml_data_content)

        models_filename = "./models/" + yaml_models_name + ".yaml"
        os.makedirs(os.path.dirname(models_filename), exist_ok=True)
        with open(models_filename, "w", encoding='utf-8') as f:
            f.write(yaml_models_content)

        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Information', 'Finish!', QMessageBox.Ok)
        msg_box.exec_()

    def work(self, text):
        myThread = RunThread()
        self.sin.connect(myThread.stop)

        if text == 'Train':
            self.update_tag = 0
            self.myThread.flag = 1
            self.myThread.start()
            sys.stdout.text_update.connect(self.updatetext)
        elif text == 'Stop Training':
            self.update_tag = 1
            self.sin.emit()
            sys.stdout.text_update.connect(self.updatetext)

    def updatetext(self, text):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser.append(text)
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    @torch.no_grad()
    def run(self,
            weights=ROOT / 'yolov5s.pt',  # model.pt path(s)
            source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
            data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
            imgsz=(640, 640),  # inference size (height, width)
            conf_thres=0.25,  # confidence threshold
            iou_thres=0.45,  # NMS IOU threshold
            max_det=1000,  # maximum detections per image
            device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
            view_img=True,  # show results
            save_txt=False,  # save results to *.txt
            save_conf=False,  # save confidences in --save-txt labels
            save_crop=False,  # save cropped prediction boxes
            nosave=False,  # do not save images/videos
            classes=None,  # filter by class: --class 0, or --class 0 2 3
            agnostic_nms=False,  # class-agnostic NMS
            augment=False,  # augmented inference
            visualize=True,  # visualize features
            update=False,  # update all models
            project=ROOT / 'runs/detect',  # save results to project/name
            name='exp',  # save results to project/name
            exist_ok=False,  # existing project/name ok, do not increment
            line_thickness=3,  # bounding box thickness (pixels)
            hide_labels=False,  # hide labels
            hide_conf=False,  # hide confidences
            half=False,  # use FP16 half-precision inference
            dnn=False,  # use OpenCV DNN for ONNX inference
    ):
        source = str(source)
        save_img = not nosave and not source.endswith('.txt')  # save inference images
        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
        if is_url and is_file:
            source = check_file(source)  # download

        # Directories
        save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
        (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

        # Load model
        device = select_device(device)
        model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(imgsz, s=stride)  # check image size

        # Dataloader
        if webcam:
            view_img = check_imshow()
            cudnn.benchmark = True  # set True to speed up constant image size inference
            dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
            bs = len(dataset)  # batch_size
        else:
            dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
            bs = 1  # batch_size
        vid_path, vid_writer = [None] * bs, [None] * bs

        # Run inference
        model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
        dt, seen = [0.0, 0.0, 0.0], 0
        for path, im, im0s, vid_cap, s in dataset:
            t1 = time_sync()
            im = torch.from_numpy(im).to(device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim
            t2 = time_sync()
            dt[0] += t2 - t1

            # Inference
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)
            t3 = time_sync()
            dt[1] += t3 - t2

            # NMS
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
            dt[2] += time_sync() - t3

            # Second-stage classifier (optional)
            # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

            # Process predictions
            for i, det in enumerate(pred):  # per image
                seen += 1
                if webcam:  # batch_size >= 1
                    p, im0, frame = path[i], im0s[i].copy(), dataset.count
                    s += f'{i}: '
                else:
                    p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

                p = Path(p)  # to Path
                save_path = str(save_dir / p.name)  # im.jpg
                txt_path = str(save_dir / 'labels' / p.stem) + (
                    '' if dataset.mode == 'image' else f'_{frame}')  # im.txt
                s += '%gx%g ' % im.shape[2:]  # print string
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                imc = im0.copy() if save_crop else im0  # for save_crop
                annotator = Annotator(im0, line_width=line_thickness, example=str(names))
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        if save_txt:  # Write to file
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                            with open(f'{txt_path}.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img or save_crop or view_img:  # Add bbox to image
                            c = int(cls)  # integer class
                            label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                            annotator.box_label(xyxy, label, color=colors(c, True))
                        if save_crop:
                            save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)

                # Stream results
                im0 = annotator.result()
                if view_img:
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond

                # Save results (image with detections)
                if save_img:
                    if dataset.mode == 'image':
                        cv2.imwrite(save_path, im0)
                    else:  # 'video' or 'stream'
                        if vid_path[i] != save_path:  # new video
                            vid_path[i] = save_path
                            if isinstance(vid_writer[i], cv2.VideoWriter):
                                vid_writer[i].release()  # release previous video writer
                            if vid_cap:  # video
                                fps = vid_cap.get(cv2.CAP_PROP_FPS)
                                w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            else:  # stream
                                fps, w, h = 30, im0.shape[1], im0.shape[0]
                            save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                            vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        vid_writer[i].write(im0)

            # Print time (inference-only)
            LOGGER.info(f'{s}Done. ({t3 - t2:.3f}s)')

        # Print results
        t = tuple(x / seen * 1E3 for x in dt)  # speeds per image
        LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
        if save_txt or save_img:
            s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
            LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
        if update:
            strip_optimizer(weights)  # update model (to fix SourceChangeWarning)

    def parse_opt(self):
        cwd = os.getcwd()
        weights_path = QFileDialog.getOpenFileName(self, "Please select the weights file", cwd, "Pt Files (*.pt);;All Files (*)")
        data_path = QFileDialog.getOpenFileName(self, "Please select the data file", cwd, "Yaml Files (*.yaml);;All Files (*)")
        print(weights_path)
        print(data_path)
        split_weights_path: list[str] = re.split(",|\(|'", str(weights_path))
        split_data_path: list[str] = re.split(",|\(|'", str(data_path))
        print(split_data_path)
        print(split_weights_path)

        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', nargs='+', type=str, default= split_weights_path[2], help='model path(s)')
        parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob, 0 for webcam')
        parser.add_argument('--data', type=str, default= split_data_path[2], help='(optional) dataset.yaml path')
        parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640],
                            help='inference size h,w')
        parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
        parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--view-img', action='store_true', help='show results')
        parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
        parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
        parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
        parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--visualize', action='store_true', help='visualize features')
        parser.add_argument('--update', action='store_true', help='update all models')
        parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
        parser.add_argument('--name', default='exp', help='save results to project/name')
        parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
        parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
        parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
        parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
        parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
        opt = parser.parse_args()
        opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
        print_args(vars(opt))
        return opt

    def main(self,opt):
        check_requirements(exclude=('tensorboard', 'thop'))
        self.run(**vars(opt))

    def detect(self):
        opt = self.parse_opt()
        self.main(opt)
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Information', 'Finish!', QMessageBox.Ok)
        msg_box.exec_()



class RunThread(QThread):
    trigger = pyqtSignal()

    def __init__(self, parent=None):
        super(RunThread, self).__init__()
        self.flag = 1

        sys.stdout = Signal()
        sys.stdout.text_update.connect(self.updatetext)

    def __del__(self):
        self.wait()

    def stop(self):
        self.flag = 0

    def train(self, hyp, opt, device, callbacks):  # hyp is path/to/hyp.yaml or hyp dictionary
        save_dir, epochs, batch_size, weights, single_cls, evolve, data, cfg, resume, noval, nosave, workers, freeze = \
            Path(opt.save_dir), opt.epochs, opt.batch_size, opt.weights, opt.single_cls, opt.evolve, opt.data, opt.cfg, \
            opt.resume, opt.noval, opt.nosave, opt.workers, opt.freeze
        callbacks.run('on_pretrain_routine_start')

        # Directories
        w = save_dir / 'weights'  # weights dir
        (w.parent if evolve else w).mkdir(parents=True, exist_ok=True)  # make dir
        last, best = w / 'last.pt', w / 'best.pt'

        # Hyperparameters
        if isinstance(hyp, str):
            with open(hyp, errors='ignore') as f:
                hyp = yaml.safe_load(f)  # load hyps dict
        LOGGER.info(colorstr('hyperparameters: ') + ', '.join(f'{k}={v}' for k, v in hyp.items()))

        # Save run settings
        if not evolve:
            with open(save_dir / 'hyp.yaml', 'w') as f:
                yaml.safe_dump(hyp, f, sort_keys=False)
            with open(save_dir / 'opt.yaml', 'w') as f:
                yaml.safe_dump(vars(opt), f, sort_keys=False)

        # Loggers
        data_dict = None
        if RANK in {-1, 0}:
            loggers = Loggers(save_dir, weights, opt, hyp, LOGGER)  # loggers instance
            if loggers.wandb:
                data_dict = loggers.wandb.data_dict
                if resume:
                    weights, epochs, hyp, batch_size = opt.weights, opt.epochs, opt.hyp, opt.batch_size

            # Register actions
            for k in methods(loggers):
                callbacks.register_action(k, callback=getattr(loggers, k))

        # Config
        plots = not evolve and not opt.noplots  # create plots
        cuda = device.type != 'cpu'
        init_seeds(1 + RANK)
        with torch_distributed_zero_first(LOCAL_RANK):
            data_dict = data_dict or check_dataset(data)  # check if None
        train_path, val_path = data_dict['train'], data_dict['val']
        nc = 1 if single_cls else int(data_dict['nc'])  # number of classes
        names = ['item'] if single_cls and len(data_dict['names']) != 1 else data_dict['names']  # class names
        assert len(names) == nc, f'{len(names)} names found for nc={nc} dataset in {data}'  # check
        is_coco = isinstance(val_path, str) and val_path.endswith('coco/val2017.txt')  # COCO dataset

        # Model
        check_suffix(weights, '.pt')  # check weights
        pretrained = weights.endswith('.pt')
        if pretrained:
            with torch_distributed_zero_first(LOCAL_RANK):
                weights = attempt_download(weights)  # download if not found locally
            ckpt = torch.load(weights, map_location='cpu')  # load checkpoint to CPU to avoid CUDA memory leak
            model = Model(cfg or ckpt['model'].yaml, ch=3, nc=nc, anchors=hyp.get('anchors')).to(device)  # create
            exclude = ['anchor'] if (cfg or hyp.get('anchors')) and not resume else []  # exclude keys
            csd = ckpt['model'].float().state_dict()  # checkpoint state_dict as FP32
            csd = intersect_dicts(csd, model.state_dict(), exclude=exclude)  # intersect
            model.load_state_dict(csd, strict=False)  # load
            LOGGER.info(f'Transferred {len(csd)}/{len(model.state_dict())} items from {weights}')  # report
        else:
            model = Model(cfg, ch=3, nc=nc, anchors=hyp.get('anchors')).to(device)  # create
        amp = check_amp(model)  # check AMP

        # Freeze
        freeze = [f'model.{x}.' for x in (freeze if len(freeze) > 1 else range(freeze[0]))]  # layers to freeze
        for k, v in model.named_parameters():
            v.requires_grad = True  # train all layers
            if any(x in k for x in freeze):
                LOGGER.info(f'freezing {k}')
                v.requires_grad = False
            QtWidgets.QApplication.processEvents()

        # Image size
        gs = max(int(model.stride.max()), 32)  # grid size (max stride)
        imgsz = check_img_size(opt.imgsz, gs, floor=gs * 2)  # verify imgsz is gs-multiple

        # Batch size
        if RANK == -1 and batch_size == -1:  # single-GPU only, estimate best batch size
            batch_size = check_train_batch_size(model, imgsz, amp)
            loggers.on_params_update({"batch_size": batch_size})

        # Optimizer
        nbs = 64  # nominal batch size
        accumulate = max(round(nbs / batch_size), 1)  # accumulate loss before optimizing
        hyp['weight_decay'] *= batch_size * accumulate / nbs  # scale weight_decay
        LOGGER.info(f"Scaled weight_decay = {hyp['weight_decay']}")

        g = [], [], []  # optimizer parameter groups
        bn = tuple(v for k, v in nn.__dict__.items() if 'Norm' in k)  # normalization layers, i.e. BatchNorm2d()
        for v in model.modules():
            if hasattr(v, 'bias') and isinstance(v.bias, nn.Parameter):  # bias
                g[2].append(v.bias)
            if isinstance(v, bn):  # weight (no decay)
                g[1].append(v.weight)
            elif hasattr(v, 'weight') and isinstance(v.weight, nn.Parameter):  # weight (with decay)
                g[0].append(v.weight)
            QtWidgets.QApplication.processEvents()

        if opt.optimizer == 'Adam':
            optimizer = Adam(g[2], lr=hyp['lr0'], betas=(hyp['momentum'], 0.999))  # adjust beta1 to momentum
        elif opt.optimizer == 'AdamW':
            optimizer = AdamW(g[2], lr=hyp['lr0'], betas=(hyp['momentum'], 0.999))  # adjust beta1 to momentum
        else:
            optimizer = SGD(g[2], lr=hyp['lr0'], momentum=hyp['momentum'], nesterov=True)

        optimizer.add_param_group({'params': g[0], 'weight_decay': hyp['weight_decay']})  # add g0 with weight_decay
        optimizer.add_param_group({'params': g[1]})  # add g1 (BatchNorm2d weights)
        LOGGER.info(f"{colorstr('optimizer:')} {type(optimizer).__name__} with parameter groups "
                    f"{len(g[1])} weight (no decay), {len(g[0])} weight, {len(g[2])} bias")
        del g

        # Scheduler
        if opt.cos_lr:
            lf = one_cycle(1, hyp['lrf'], epochs)  # cosine 1->hyp['lrf']
        else:
            lf = lambda x: (1 - x / epochs) * (1.0 - hyp['lrf']) + hyp['lrf']  # linear
        scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lf)  # plot_lr_scheduler(optimizer, scheduler, epochs)

        # EMA
        ema = ModelEMA(model) if RANK in {-1, 0} else None

        # Resume
        start_epoch, best_fitness = 0, 0.0
        if pretrained:
            # Optimizer
            if ckpt['optimizer'] is not None:
                optimizer.load_state_dict(ckpt['optimizer'])
                best_fitness = ckpt['best_fitness']

            # EMA
            if ema and ckpt.get('ema'):
                ema.ema.load_state_dict(ckpt['ema'].float().state_dict())
                ema.updates = ckpt['updates']

            # Epochs
            start_epoch = ckpt['epoch'] + 1
            if resume:
                assert start_epoch > 0, f'{weights} training to {epochs} epochs is finished, nothing to resume.'
            if epochs < start_epoch:
                LOGGER.info(
                    f"{weights} has been trained for {ckpt['epoch']} epochs. Fine-tuning for {epochs} more epochs.")
                epochs += ckpt['epoch']  # finetune additional epochs

            del ckpt, csd

        # DP mode
        if cuda and RANK == -1 and torch.cuda.device_count() > 1:
            LOGGER.warning('WARNING: DP not recommended, use torch.distributed.run for best DDP Multi-GPU results.\n'
                           'See Multi-GPU Tutorial at https://github.com/ultralytics/yolov5/issues/475 to get started.')
            model = torch.nn.DataParallel(model)

        # SyncBatchNorm
        if opt.sync_bn and cuda and RANK != -1:
            model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model).to(device)
            LOGGER.info('Using SyncBatchNorm()')

        # Trainloader
        train_loader, dataset = create_dataloader(train_path,
                                                  imgsz,
                                                  batch_size // WORLD_SIZE,
                                                  gs,
                                                  single_cls,
                                                  hyp=hyp,
                                                  augment=True,
                                                  cache=None if opt.cache == 'val' else opt.cache,
                                                  rect=opt.rect,
                                                  rank=LOCAL_RANK,
                                                  workers=workers,
                                                  image_weights=opt.image_weights,
                                                  quad=opt.quad,
                                                  prefix=colorstr('train: '),
                                                  shuffle=True)
        mlc = int(np.concatenate(dataset.labels, 0)[:, 0].max())  # max label class
        nb = len(train_loader)  # number of batches
        assert mlc < nc, f'Label class {mlc} exceeds nc={nc} in {data}. Possible class labels are 0-{nc - 1}'

        # Process 0
        if RANK in {-1, 0}:
            val_loader = create_dataloader(val_path,
                                           imgsz,
                                           batch_size // WORLD_SIZE * 2,
                                           gs,
                                           single_cls,
                                           hyp=hyp,
                                           cache=None if noval else opt.cache,
                                           rect=True,
                                           rank=-1,
                                           workers=workers * 2,
                                           pad=0.5,
                                           prefix=colorstr('val: '))[0]

            if not resume:
                labels = np.concatenate(dataset.labels, 0)
                # c = torch.tensor(labels[:, 0])  # classes
                # cf = torch.bincount(c.long(), minlength=nc) + 1.  # frequency
                # model._initialize_biases(cf.to(device))
                if plots:
                    plot_labels(labels, names, save_dir)

                # Anchors
                if not opt.noautoanchor:
                    check_anchors(dataset, model=model, thr=hyp['anchor_t'], imgsz=imgsz)
                model.half().float()  # pre-reduce anchor precision

            callbacks.run('on_pretrain_routine_end')

        # DDP mode
        if cuda and RANK != -1:
            if check_version(torch.__version__, '1.11.0'):
                model = DDP(model, device_ids=[LOCAL_RANK], output_device=LOCAL_RANK, static_graph=True)
            else:
                model = DDP(model, device_ids=[LOCAL_RANK], output_device=LOCAL_RANK)

        # Model attributes
        nl = de_parallel(model).model[-1].nl  # number of detection layers (to scale hyps)
        hyp['box'] *= 3 / nl  # scale to layers
        hyp['cls'] *= nc / 80 * 3 / nl  # scale to classes and layers
        hyp['obj'] *= (imgsz / 640) ** 2 * 3 / nl  # scale to image size and layers
        hyp['label_smoothing'] = opt.label_smoothing
        model.nc = nc  # attach number of classes to model
        model.hyp = hyp  # attach hyperparameters to model
        model.class_weights = labels_to_class_weights(dataset.labels, nc).to(device) * nc  # attach class weights
        model.names = names

        # Start training
        t0 = time.time()
        nw = max(round(hyp['warmup_epochs'] * nb), 100)  # number of warmup iterations, max(3 epochs, 100 iterations)
        # nw = min(nw, (epochs - start_epoch) / 2 * nb)  # limit warmup to < 1/2 of training
        last_opt_step = -1
        maps = np.zeros(nc)  # mAP per class
        results = (0, 0, 0, 0, 0, 0, 0)  # P, R, mAP@.5, mAP@.5-.95, val_loss(box, obj, cls)
        scheduler.last_epoch = start_epoch - 1  # do not move
        scaler = torch.cuda.amp.GradScaler(enabled=amp)
        stopper = EarlyStopping(patience=opt.patience)
        compute_loss = ComputeLoss(model)  # init loss class
        callbacks.run('on_train_start')
        LOGGER.info(f'Image sizes {imgsz} train, {imgsz} val\n'
                    f'Using {train_loader.num_workers * WORLD_SIZE} dataloader workers\n'
                    f"Logging results to {colorstr('bold', save_dir)}\n"
                    f'Starting training for {epochs} epochs...')
        # sys.stdout = Signal()
        for epoch in range(start_epoch,
                           epochs):  # epoch ------------------------------------------------------------------
            if self.flag == 1:
                print("epoch = "+str(epoch))
                # sys.stdout.text_update.connect(self.updatetext)
                QtWidgets.QApplication.processEvents()

                callbacks.run('on_train_epoch_start')
                model.train()

                # Update image weights (optional, single-GPU only)
                if opt.image_weights:
                    cw = model.class_weights.cpu().numpy() * (1 - maps) ** 2 / nc  # class weights
                    iw = labels_to_image_weights(dataset.labels, nc=nc, class_weights=cw)  # image weights
                    dataset.indices = random.choices(range(dataset.n), weights=iw, k=dataset.n)  # rand weighted idx

                # Update mosaic border (optional)
                # b = int(random.uniform(0.25 * imgsz, 0.75 * imgsz + gs) // gs * gs)
                # dataset.mosaic_border = [b - imgsz, -b]  # height, width borders

                mloss = torch.zeros(3, device=device)  # mean losses
                if RANK != -1:
                    train_loader.sampler.set_epoch(epoch)
                pbar = enumerate(train_loader)
                LOGGER.info(('\n' + '%10s' * 7) % ('Epoch', 'gpu_mem', 'box', 'obj', 'cls', 'labels', 'img_size'))
                if RANK in {-1, 0}:
                    pbar = tqdm(pbar, total=nb, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}')  # progress bar
                optimizer.zero_grad()
                for i, (
                imgs, targets, paths, _) in pbar:  # batch -------------------------------------------------------------
                    callbacks.run('on_train_batch_start')
                    ni = i + nb * epoch  # number integrated batches (since train start)
                    imgs = imgs.to(device, non_blocking=True).float() / 255  # uint8 to float32, 0-255 to 0.0-1.0

                    # Warmup
                    if ni <= nw:
                        xi = [0, nw]  # x interp
                        # compute_loss.gr = np.interp(ni, xi, [0.0, 1.0])  # iou loss ratio (obj_loss = 1.0 or iou)
                        accumulate = max(1, np.interp(ni, xi, [1, nbs / batch_size]).round())
                        for j, x in enumerate(optimizer.param_groups):
                            # bias lr falls from 0.1 to lr0, all other lrs rise from 0.0 to lr0
                            x['lr'] = np.interp(ni, xi,
                                                [hyp['warmup_bias_lr'] if j == 2 else 0.0, x['initial_lr'] * lf(epoch)])
                            if 'momentum' in x:
                                x['momentum'] = np.interp(ni, xi, [hyp['warmup_momentum'], hyp['momentum']])

                    # Multi-scale
                    if opt.multi_scale:
                        sz = random.randrange(imgsz * 0.5, imgsz * 1.5 + gs) // gs * gs  # size
                        sf = sz / max(imgs.shape[2:])  # scale factor
                        if sf != 1:
                            ns = [math.ceil(x * sf / gs) * gs for x in
                                  imgs.shape[2:]]  # new shape (stretched to gs-multiple)
                            imgs = nn.functional.interpolate(imgs, size=ns, mode='bilinear', align_corners=False)

                    # Forward
                    with torch.cuda.amp.autocast(amp):
                        pred = model(imgs)  # forward
                        loss, loss_items = compute_loss(pred, targets.to(device))  # loss scaled by batch_size
                        if RANK != -1:
                            loss *= WORLD_SIZE  # gradient averaged between devices in DDP mode
                        if opt.quad:
                            loss *= 4.

                    # Backward
                    scaler.scale(loss).backward()

                    # Optimize
                    if ni - last_opt_step >= accumulate:
                        scaler.step(optimizer)  # optimizer.step
                        scaler.update()
                        optimizer.zero_grad()
                        if ema:
                            ema.update(model)
                        last_opt_step = ni

                    # Log
                    if RANK in {-1, 0}:
                        mloss = (mloss * i + loss_items) / (i + 1)  # update mean losses
                        mem = f'{torch.cuda.memory_reserved() / 1E9 if torch.cuda.is_available() else 0:.3g}G'  # (GB)
                        pbar.set_description(('%10s' * 2 + '%10.4g' * 5) %
                                             (f'{epoch}/{epochs - 1}', mem, *mloss, targets.shape[0], imgs.shape[-1]))
                        callbacks.run('on_train_batch_end', ni, model, imgs, targets, paths, plots)
                        if callbacks.stop_training:
                            return
                    # end batch ------------------------------------------------------------------------------------------------

                # Scheduler
                lr = [x['lr'] for x in optimizer.param_groups]  # for loggers
                scheduler.step()

                if RANK in {-1, 0}:
                    # mAP
                    callbacks.run('on_train_epoch_end', epoch=epoch)
                    ema.update_attr(model, include=['yaml', 'nc', 'hyp', 'names', 'stride', 'class_weights'])
                    final_epoch = (epoch + 1 == epochs) or stopper.possible_stop
                    if not noval or final_epoch:  # Calculate mAP
                        results, maps, _ = val.run(data_dict,
                                                   batch_size=batch_size // WORLD_SIZE * 2,
                                                   imgsz=imgsz,
                                                   model=ema.ema,
                                                   single_cls=single_cls,
                                                   dataloader=val_loader,
                                                   save_dir=save_dir,
                                                   plots=False,
                                                   callbacks=callbacks,
                                                   compute_loss=compute_loss)

                    # Update best mAP
                    fi = fitness(np.array(results).reshape(1, -1))  # weighted combination of [P, R, mAP@.5, mAP@.5-.95]
                    if fi > best_fitness:
                        best_fitness = fi
                    log_vals = list(mloss) + list(results) + lr
                    callbacks.run('on_fit_epoch_end', log_vals, epoch, best_fitness, fi)

                    # Save model
                    if (not nosave) or (final_epoch and not evolve):  # if save
                        ckpt = {
                            'epoch': epoch,
                            'best_fitness': best_fitness,
                            'model': deepcopy(de_parallel(model)).half(),
                            'ema': deepcopy(ema.ema).half(),
                            'updates': ema.updates,
                            'optimizer': optimizer.state_dict(),
                            'wandb_id': loggers.wandb.wandb_run.id if loggers.wandb else None,
                            'date': datetime.now().isoformat()}

                        # Save last, best and delete
                        torch.save(ckpt, last)
                        if best_fitness == fi:
                            torch.save(ckpt, best)
                        if opt.save_period > 0 and epoch % opt.save_period == 0:
                            torch.save(ckpt, w / f'epoch{epoch}.pt')
                        del ckpt
                        callbacks.run('on_model_save', last, epoch, final_epoch, best_fitness, fi)

                    # Stop Single-GPU
                    if RANK == -1 and stopper(epoch=epoch, fitness=fi):
                        break

                    # Stop DDP TODO: known issues shttps://github.com/ultralytics/yolov5/pull/4576
                    # stop = stopper(epoch=epoch, fitness=fi)
                    # if RANK == 0:
                    #    dist.broadcast_object_list([stop], 0)  # broadcast 'stop' to all ranks

            elif self.flag == 0:
                break

            # Stop DPP
            # with torch_distributed_zero_first(RANK):
            # if stop:
            #    break  # must break all DDP ranks

            # end epoch ----------------------------------------------------------------------------------------------------
        # end training -----------------------------------------------------------------------------------------------------
        if RANK in {-1, 0}:
            LOGGER.info(f'\n{epoch - start_epoch + 1} epochs completed in {(time.time() - t0) / 3600:.3f} hours.')
            for f in last, best:
                if f.exists():
                    strip_optimizer(f)  # strip optimizers
                    if f is best:
                        LOGGER.info(f'\nValidating {f}...')
                        results, _, _ = val.run(
                            data_dict,
                            batch_size=batch_size // WORLD_SIZE * 2,
                            imgsz=imgsz,
                            model=attempt_load(f, device).half(),
                            iou_thres=0.65 if is_coco else 0.60,  # best pycocotools results at 0.65
                            single_cls=single_cls,
                            dataloader=val_loader,
                            save_dir=save_dir,
                            save_json=is_coco,
                            verbose=True,
                            plots=plots,
                            callbacks=callbacks,
                            compute_loss=compute_loss)  # val best model with plots
                        if is_coco:
                            callbacks.run('on_fit_epoch_end', list(mloss) + list(results) + lr, epoch, best_fitness, fi)

            callbacks.run('on_train_end', last, best, plots, epoch, results)

        torch.cuda.empty_cache()

        QtWidgets.QApplication.processEvents()

        self.trigger.emit()
        return results

    def parse_opt(self, known=False):

        mwindow = mainwindow()

        weights = mwindow.Weights_comboBox.currentText()
        cfg = "models/" + mwindow.cfg_lineEdit.text() + ".yaml"
        data = "data/" + mwindow.data_lineEdit.text() + ".yaml"
        epochs = int(mwindow.epochs_lineEdit.text())
        bs = int(mwindow.bs_lineEdit.text())

        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', type=str, default=ROOT / weights, help='initial weights path')
        parser.add_argument('--cfg', type=str, default=ROOT / cfg, help='model.yaml path')
        parser.add_argument('--data', type=str, default=ROOT / data, help='dataset.yaml path')
        parser.add_argument('--hyp', type=str, default=ROOT / 'data/hyps/hyp.scratch-low.yaml',
                            help='hyperparameters path')
        parser.add_argument('--epochs', type=int, default=epochs)
        parser.add_argument('--batch-size', type=int, default=bs,
                            help='total batch size for all GPUs, -1 for autobatch')
        parser.add_argument('--imgsz', '--img', '--img-size', type=int, default=640,
                            help='train, val image size (pixels)')
        parser.add_argument('--rect', action='store_true', help='rectangular training')
        parser.add_argument('--resume', nargs='?', const=True, default=False, help='resume most recent training')
        parser.add_argument('--nosave', action='store_true', help='only save final checkpoint')
        parser.add_argument('--noval', action='store_true', help='only validate final epoch')
        parser.add_argument('--noautoanchor', action='store_true', help='disable AutoAnchor')
        parser.add_argument('--noplots', action='store_true', help='save no plot files')
        parser.add_argument('--evolve', type=int, nargs='?', const=300, help='evolve hyperparameters for x generations')
        parser.add_argument('--bucket', type=str, default='', help='gsutil bucket')
        parser.add_argument('--cache', type=str, nargs='?', const='ram',
                            help='--cache images in "ram" (default) or "disk"')
        parser.add_argument('--image-weights', action='store_true', help='use weighted image selection for training')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--multi-scale', action='store_true', help='vary img-size +/- 50%%')
        parser.add_argument('--single-cls', action='store_true', help='train multi-class data as single-class')
        parser.add_argument('--optimizer', type=str, choices=['SGD', 'Adam', 'AdamW'], default='SGD', help='optimizer')
        parser.add_argument('--sync-bn', action='store_true', help='use SyncBatchNorm, only available in DDP mode')
        parser.add_argument('--workers', type=int, default=8, help='max dataloader workers (per RANK in DDP mode)')
        parser.add_argument('--project', default=ROOT / 'runs/train', help='save to project/name')
        parser.add_argument('--name', default='exp', help='save to project/name')
        parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--quad', action='store_true', help='quad dataloader')
        parser.add_argument('--cos-lr', action='store_true', help='cosine LR scheduler')
        parser.add_argument('--label-smoothing', type=float, default=0.0, help='Label smoothing epsilon')
        parser.add_argument('--patience', type=int, default=100,
                            help='EarlyStopping patience (epochs without improvement)')
        parser.add_argument('--freeze', nargs='+', type=int, default=[0],
                            help='Freeze layers: backbone=10, first3=0 1 2')
        parser.add_argument('--save-period', type=int, default=-1,
                            help='Save checkpoint every x epochs (disabled if < 1)')
        parser.add_argument('--local_rank', type=int, default=-1, help='DDP parameter, do not modify')

        # Weights & Biases arguments
        parser.add_argument('--entity', default=None, help='W&B: Entity')
        parser.add_argument('--upload_dataset', nargs='?', const=True, default=False,
                            help='W&B: Upload data, "val" option')
        parser.add_argument('--bbox_interval', type=int, default=-1,
                            help='W&B: Set bounding-box image logging interval')
        parser.add_argument('--artifact_alias', type=str, default='latest',
                            help='W&B: Version of dataset artifact to use')

        opt = parser.parse_known_args()[0] if known else parser.parse_args()

        QtWidgets.QApplication.processEvents()
        return opt

    def main(self, opt, callbacks=Callbacks()):
        # Checks
        if RANK in {-1, 0}:
            print_args(vars(opt))
            check_git_status()
            check_requirements(exclude=['thop'])

        # Resume
        if opt.resume and not check_wandb_resume(opt) and not opt.evolve:  # resume an interrupted run
            ckpt = opt.resume if isinstance(opt.resume, str) else get_latest_run()  # specified or most recent path
            assert os.path.isfile(ckpt), 'ERROR: --resume checkpoint does not exist'
            with open(Path(ckpt).parent.parent / 'opt.yaml', errors='ignore') as f:
                opt = argparse.Namespace(**yaml.safe_load(f))  # replace
            opt.cfg, opt.weights, opt.resume = '', ckpt, True  # reinstate
            LOGGER.info(f'Resuming training from {ckpt}')
        else:
            opt.data, opt.cfg, opt.hyp, opt.weights, opt.project = \
                check_file(opt.data), check_yaml(opt.cfg), check_yaml(opt.hyp), str(opt.weights), str(
                    opt.project)  # checks
            assert len(opt.cfg) or len(opt.weights), 'either --cfg or --weights must be specified'
            if opt.evolve:
                if opt.project == str(ROOT / 'runs/train'):  # if default project name, rename to runs/evolve
                    opt.project = str(ROOT / 'runs/evolve')
                opt.exist_ok, opt.resume = opt.resume, False  # pass resume to exist_ok and disable resume
            if opt.name == 'cfg':
                opt.name = Path(opt.cfg).stem  # use model.yaml as name
            opt.save_dir = str(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))

        # DDP mode
        device = select_device(opt.device, batch_size=opt.batch_size)
        if LOCAL_RANK != -1:
            msg = 'is not compatible with YOLOv5 Multi-GPU DDP training'
            assert not opt.image_weights, f'--image-weights {msg}'
            assert not opt.evolve, f'--evolve {msg}'
            assert opt.batch_size != -1, f'AutoBatch with --batch-size -1 {msg}, please pass a valid --batch-size'
            assert opt.batch_size % WORLD_SIZE == 0, f'--batch-size {opt.batch_size} must be multiple of WORLD_SIZE'
            assert torch.cuda.device_count() > LOCAL_RANK, 'insufficient CUDA devices for DDP command'
            torch.cuda.set_device(LOCAL_RANK)
            device = torch.device('cuda', LOCAL_RANK)
            dist.init_process_group(backend="nccl" if dist.is_nccl_available() else "gloo")

        # Train
        if not opt.evolve:
            self.train(opt.hyp, opt, device, callbacks)
            if WORLD_SIZE > 1 and RANK == 0:
                LOGGER.info('Destroying process group... ')
                dist.destroy_process_group()

        # Evolve hyperparameters (optional)
        else:
            # Hyperparameter evolution metadata (mutation scale 0-1, lower_limit, upper_limit)
            meta = {
                'lr0': (1, 1e-5, 1e-1),  # initial learning rate (SGD=1E-2, Adam=1E-3)
                'lrf': (1, 0.01, 1.0),  # final OneCycleLR learning rate (lr0 * lrf)
                'momentum': (0.3, 0.6, 0.98),  # SGD momentum/Adam beta1
                'weight_decay': (1, 0.0, 0.001),  # optimizer weight decay
                'warmup_epochs': (1, 0.0, 5.0),  # warmup epochs (fractions ok)
                'warmup_momentum': (1, 0.0, 0.95),  # warmup initial momentum
                'warmup_bias_lr': (1, 0.0, 0.2),  # warmup initial bias lr
                'box': (1, 0.02, 0.2),  # box loss gain
                'cls': (1, 0.2, 4.0),  # cls loss gain
                'cls_pw': (1, 0.5, 2.0),  # cls BCELoss positive_weight
                'obj': (1, 0.2, 4.0),  # obj loss gain (scale with pixels)
                'obj_pw': (1, 0.5, 2.0),  # obj BCELoss positive_weight
                'iou_t': (0, 0.1, 0.7),  # IoU training threshold
                'anchor_t': (1, 2.0, 8.0),  # anchor-multiple threshold
                'anchors': (2, 2.0, 10.0),  # anchors per output grid (0 to ignore)
                'fl_gamma': (0, 0.0, 2.0),  # focal loss gamma (efficientDet default gamma=1.5)
                'hsv_h': (1, 0.0, 0.1),  # image HSV-Hue augmentation (fraction)
                'hsv_s': (1, 0.0, 0.9),  # image HSV-Saturation augmentation (fraction)
                'hsv_v': (1, 0.0, 0.9),  # image HSV-Value augmentation (fraction)
                'degrees': (1, 0.0, 45.0),  # image rotation (+/- deg)
                'translate': (1, 0.0, 0.9),  # image translation (+/- fraction)
                'scale': (1, 0.0, 0.9),  # image scale (+/- gain)
                'shear': (1, 0.0, 10.0),  # image shear (+/- deg)
                'perspective': (0, 0.0, 0.001),  # image perspective (+/- fraction), range 0-0.001
                'flipud': (1, 0.0, 1.0),  # image flip up-down (probability)
                'fliplr': (0, 0.0, 1.0),  # image flip left-right (probability)
                'mosaic': (1, 0.0, 1.0),  # image mixup (probability)
                'mixup': (1, 0.0, 1.0),  # image mixup (probability)
                'copy_paste': (1, 0.0, 1.0)}  # segment copy-paste (probability)

            with open(opt.hyp, errors='ignore') as f:
                hyp = yaml.safe_load(f)  # load hyps dict
                if 'anchors' not in hyp:  # anchors commented in hyp.yaml
                    hyp['anchors'] = 3
            opt.noval, opt.nosave, save_dir = True, True, Path(opt.save_dir)  # only val/save final epoch
            # ei = [isinstance(x, (int, float)) for x in hyp.values()]  # evolvable indices
            evolve_yaml, evolve_csv = save_dir / 'hyp_evolve.yaml', save_dir / 'evolve.csv'
            if opt.bucket:
                os.system(f'gsutil cp gs://{opt.bucket}/evolve.csv {evolve_csv}')  # download evolve.csv if exists

            for _ in range(opt.evolve):  # generations to evolve
                if evolve_csv.exists():  # if evolve.csv exists: select best hyps and mutate
                    # Select parent(s)
                    parent = 'single'  # parent selection method: 'single' or 'weighted'
                    x = np.loadtxt(evolve_csv, ndmin=2, delimiter=',', skiprows=1)
                    n = min(5, len(x))  # number of previous results to consider
                    x = x[np.argsort(-fitness(x))][:n]  # top n mutations
                    w = fitness(x) - fitness(x).min() + 1E-6  # weights (sum > 0)
                    if parent == 'single' or len(x) == 1:
                        # x = x[random.randint(0, n - 1)]  # random selection
                        x = x[random.choices(range(n), weights=w)[0]]  # weighted selection
                    elif parent == 'weighted':
                        x = (x * w.reshape(n, 1)).sum(0) / w.sum()  # weighted combination

                    # Mutate
                    mp, s = 0.8, 0.2  # mutation probability, sigma
                    npr = np.random
                    npr.seed(int(time.time()))
                    g = np.array([meta[k][0] for k in hyp.keys()])  # gains 0-1
                    ng = len(meta)
                    v = np.ones(ng)
                    while all(v == 1):  # mutate until a change occurs (prevent duplicates)
                        v = (g * (npr.random(ng) < mp) * npr.randn(ng) * npr.random() * s + 1).clip(0.3, 3.0)
                    for i, k in enumerate(hyp.keys()):  # plt.hist(v.ravel(), 300)
                        hyp[k] = float(x[i + 7] * v[i])  # mutate

                # Constrain to limits
                for k, v in meta.items():
                    hyp[k] = max(hyp[k], v[1])  # lower limit
                    hyp[k] = min(hyp[k], v[2])  # upper limit
                    hyp[k] = round(hyp[k], 5)  # significant digits

                # Train mutation
                results = self.train(hyp.copy(), opt, device, callbacks)
                callbacks = Callbacks()
                # Write mutation results
                print_mutation(results, hyp.copy(), save_dir, opt.bucket)

            # Plot results
            plot_evolve(evolve_csv)
            LOGGER.info(f'Hyperparameter evolution finished {opt.evolve} generations\n'
                        f"Results saved to {colorstr('bold', save_dir)}\n"
                        f'Usage example: $ python train.py --hyp {evolve_yaml}')

        QtWidgets.QApplication.processEvents()

    def run(self, **kwargs):
        # Usage: import train; train.run(data='coco128.yaml', imgsz=320, weights='yolov5m.pt')
        opt = self.parse_opt(True)
        for k, v in kwargs.items():
            setattr(opt, k, v)
        self.main(opt)
        QtWidgets.QApplication.processEvents()
        return opt

    def train_t(self):
        QtWidgets.QApplication.processEvents()
        opt = self.parse_opt()
        self.main(opt)
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Information', 'Finish!', QMessageBox.Ok)
        msg_box.exec_()

    def updatetext(self, text):
        mwindow = mainwindow()
        cursor = mwindow.textBrowser.textCursor()
        cursor.movePosition(QTextCursor.End)
        mwindow.textBrowser.append(text)
        mwindow.textBrowser.setTextCursor(cursor)
        mwindow.textBrowser.ensureCursorVisible()

class Signal(QObject):

    text_update = pyqtSignal(str)

    def write(self, text):
        self.text_update.emit(str(text))
        QApplication.processEvents()






if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wshow = mainwindow()
    wshow.show()
    sys.exit(app.exec_())
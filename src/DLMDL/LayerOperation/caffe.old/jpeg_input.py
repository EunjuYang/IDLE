# -*- coding: utf-8 -*-
from ..layer_operation import LayerOperation
import numpy as np
from scipy.misc import imread
from scipy.misc import imresize
import random
import csv
import sys
import caffe
from caffe import layers as L

from src.DLMDL.caffe_adaptor import tempNet # TODO: DLMDL에 solver 따로 만들거나 변경시 재검토 필요

class op_caffe_jpeg_input(LayerOperation):

    _attributes = """[{"default": "datasets", "source": "opt", "mandatory": "all", "name": "option"}, {"default": "jpg", "source": "opt", "mandatory": "all", "name": "file_format"}, {"source": "opt", "mandatory": "all", "name": "data_path"}, {"source": "opt", "mandatory": "all", "name": "label_path"}, {"source": "opt", "mandatory": "all", "name": "batch_size"}, {"source": "opt", "mandatory": "all", "name": "iteration"}, {"source": "layer", "mandatory": "all", "name": "image_size"}, {"source": "layer", "mandatory": "all", "name": "output_shape"}]"""

    def compile_time_operation(self, learning_option, cluster):
        option = learning_option.get("option", self.option)
        file_format = learning_option.get("file_format", self.file_format)
        data_path = learning_option.get("data_path", self.data_path)
        label_path = learning_option.get("label_path", self.label_path)
        batch_size = learning_option.get("batch_size", self.batch_size)
        iteration = learning_option.get("iteration", self.iteration)
        image_size = self.image_size
        output_shape = self.output_shape
        
        # for shmcaffe
        #learning_option["move_rate"] = learning_option.get("move_rate", 0.2)
        #learning_option["tau"] = learning_option.get("tau", 1)

        # Phase checkpoint setting, PHASE: 0 for trian, 1 for test
        isTrainTest = 0
        if option.lower() == "test":
            temp_include = dict(phase=caffe.TEST)
            data_path = learning_option.get("test_data_path", data_path)
            test_label_path = learning_option.get("test_label_path", label_path)
            batch_size = learning_option.get("test_batch_size", batch_size)
        elif option.lower() == "datasets":
            temp_include = dict(phase=caffe.TRAIN)
        elif option.lower() == "train_test":
            temp_include = dict(phase=caffe.TRAIN)
            isTrainTest = 1
        else:
            temp_include = dict(phase=caffe.TRAIN)

        # DB Data
        if file_format.lower() in ["lmdb", "leveldb"]:
            # Backend checkpoint setting, default value 0 (leveldb) for backend
            # Data layer setting
            image, label = L.Data(name=self.name, source=data_path,
                             batch_size=batch_size, backend=(0 if file_format.lower()=="leveldb" else 1), include=temp_include, ntop=2)

            if isTrainTest == 1:
                data_path = learning_option.get("test_data_path", data_path)
                batch_size = learning_option.get("test_batch_size", batch_size)
                temp_image, temp_label = L.Data(name=self.name, source=data_path,
                                                batch_size=batch_size,
                                                backend=(0 if file_format.lower() == "leveldb" else 1),
                                                include=dict(phase=caffe.TEST), ntop=2)
                setattr(tempNet, str(self.name) + '.image', temp_image)
                setattr(tempNet, str(self.name) + '.label', temp_label)

        # Image Data
        # TODO: HDF5 와 같은 형식을 또 다른 개별 종륭의 layer 사용 가능하나 현재 raw image 파일 형식만 들어온다고 가정
        else :
            # Read and parse the source directory
            
            ''' for uninfo -twkim
            with open(data_path+'/'+label_path, 'r') as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                new_lines.append('/'+line.split()[0]+'.'+file_format + ' ' + line.split()[1]+'\n')
            with open(data_path+'/'+label_path.split('.')[0]+'_caffelist.txt', 'w') as f:
                f.writelines(new_lines)
                f.close()
            '''
            
            # Image Data layer setting
            image, label = L.ImageData(name=self.name,
                                       source=data_path + '/' + label_path.split('.')[0] + '_caffelist.txt',
                                       batch_size=batch_size, include=temp_include, ntop=2, root_folder=data_path,
                                       new_height=image_size[1], new_width=image_size[0])

            if isTrainTest == 1:
                data_path = learning_option.get("test_data_path", data_path)
                batch_size = learning_option.get("test_batch_size", batch_size)
                label_path = learning_option.get("test_label_path", label_path)

                # Read and parse the source directory
                ''' for uninfo - twkim
                with open(data_path + '/' + label_path, 'r') as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    new_lines.append('/' + line.split()[0] + '.' + file_format + ' ' + line.split()[1] + '\n')
                with open(data_path + '/' + label_path.split('.')[0] + '_caffelist.txt', 'w') as f:
                    f.writelines(new_lines)
                    f.close()
                '''
                # Test image data layer setting
                temp_image, temp_label = L.ImageData(name=self.name,
                                                     source=data_path + '/' + label_path.split('.')[0] + '_caffelist.txt',
                                                     batch_size=batch_size, include=dict(phase=caffe.TEST), ntop=2,
                                                     root_folder=data_path, new_height=image_size[1],
                                                     new_width=image_size[0])
                setattr(tempNet, str(self.name) + '.image', temp_image)
                setattr(tempNet, str(self.name) + '.label', temp_label)

        # Record the layer output information
        self.set_output('image', image)
        self.set_output('label', label)
        self.set_dimension('image', image_size)
        try:
            if isTrainTest != 1:
                del learning_option['option']
            del learning_option['file_format']
            del learning_option['data_path']
            del learning_option['label_path']
            del learning_option['batch_size']
            del learning_option['iteration']
            learning_option['max_iter'] = iteration
        except KeyError:
            pass

        try:
            del learning_option['test_data_path']
            del learning_option['test_label_path']
            del learning_option['test_batch_size']
            learning_option['test_iter'] = learning_option.get("test_iteration", 100)
            del learning_option['test_iteration']
        except KeyError:
            pass

    def run_time_operation(self, learning_option, cluster):
        pass

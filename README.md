# AI-recognition-tool(Demo Version)
This is the AI recognition tool based on Labeling and YoloV5, you can do labelling, training your own model and detection.If you want to use this tool, you can follow the steps below:
1. Move the files to the root of YOLOV5;
2. Open Main.py file and run;
3. Place your training dataset in the directory of "./VOC2007/JPEGImages/";
4. Click on "Open Labeling" button to start your labeling;
5. Fill the information of your class number and their name;
6. Fill the information of trainval percentage and train percentage;
7. Click on "Convert Dataset" button to convert the images and label files for training;
8. Fill the information of the yaml file(Yaml File Name(data), Yaml File Name(models), depth multiple, width multiple);
9. Click on "Creat Yaml File" button to creat the configuration file for training;
10. Fill the information for training(Weights, Cfg Name, Data Name, Epochs, Batch-size);
11. Click on "Train" button to start training. If you want to stop your training, you can click on "Stop Training" button;
12. Click on "Detect" button then select the relevant pt and yaml file to start the detection. 

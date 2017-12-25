import os
import os.path
import re


def FindSubPath(path):
    files = []

    temp_files = os.listdir(path)

    for temp_file in temp_files:
        # full path
        full_path = os.path.join(path, temp_file)

        if os.path.isfile(full_path) and os.path.splitext(full_path)[1] == ".md":
            # print('add' + full_path)
            files.append(full_path)
        elif os.path.isdir(full_path):
            # print('dir' + full_path)
            files.extend(FindSubPath(full_path))

    return files


def FindPics(file_path):
    f = open(file_path, 'r')
    content = f.read()

    pics = []
    results = re.findall(r"!\[(.+?)\)", content)
    for result in results:
        temp_pic = result.split("](")
        pics.append({'name': temp_pic[0], 'url': temp_pic[1]})

    for pic in pics:
        print (pic['name']+':'+pic['url'])


def Find(root_path):
    files = FindSubPath(root_path)
    file = files[0]
    FindPics(file)
    # new dir
    # image_file = file.replace(".md", "_Image")
    # os.mkdir(image_file)








# root_path = input()
# FindPaths(root_path)
Find("/Users/xietao/Desktop/files/user-1319710-1513223040")





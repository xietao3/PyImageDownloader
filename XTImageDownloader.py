#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import os.path
import re
import urllib2
from Tkinter import *
import tkFileDialog
import threading


class Picture(object):

    def __init__(self, name, url, dir_path, index):
        self.index = index
        self.name = name
        self.url = url
        self.dir_path = dir_path
        self.error_reason = None

    def start_download_pic(self, download_pic_callback):
        pic_path = self.build_pic_name()

        # 已存在
        if os.path.exists(pic_path):
            print ('pic has existed:' + self.url)
            self.error_reason = "pic has existed:"
            download_pic_callback(self)
            return

        # 图片链接前缀不包含http
        if not self.url.startswith("http"):
            print ('pic has invalid url:' + self.url)
            self.error_reason = "pic has invalid url"
            download_pic_callback(self)
            return

        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
            'Cookie': 'AspxAutoDetectCookieSupport=1',
        }

        # 下载图片
        request = urllib2.Request(self.url, None, header)
        try:
            response = urllib2.urlopen(request, timeout=10)
        except Exception, error:
            print ('pic cannot download:' + self.url)
            self.error_reason = str(error)
            download_pic_callback(self)
            return

        # 保存图片
        try:
            fp = open(pic_path, 'wb')
            fp.write(response.read())
            fp.close()
        except IOError, error:
            print(error)
            self.error_reason = str(error)
            download_pic_callback(self)
            return
        # finish download this pic
        download_pic_callback(self)

    def build_pic_name(self):
        pic_url = self.url.split("?")[0]

        urls = pic_url.split(".")
        if len(urls) > 1:
            pic_type = urls[len(urls)-1]
        else:
            pic_type = "jpg"

        if self.name is not None and len(self.name) > 0:
            pic_name = self.name + "." + pic_type
        else:
            pic_name = "no_name_" + str(self.index) + "." + pic_type

        pic_path = os.path.join(self.dir_path, pic_name)
        return pic_path


class Article(object):

    def __init__(self, path):
        self.article_path = path
        self.article_pic_dir = path.replace(".md", "_Image")
        # new image dir
        self.mkdir_image_dir()
        # search pic
        self.pic_list = self.find_pics(self.article_path)

    def find_pics(self, article_path):
        f = open(article_path, 'r')
        content = f.read()
        pics = []

        # match ![]()
        results = re.findall(r"!\[(.+?)\)", content)

        index = 0
        for result in results:
            temp_pic = result.split("](")
            if len(temp_pic) == 2:
                pic = Picture(temp_pic[0], temp_pic[1], self.article_pic_dir, index)
                pics.append(pic)
            index += 1

        return pics

    def mkdir_image_dir(self):
        if not os.path.exists(self.article_pic_dir):
            os.mkdir(self.article_pic_dir)


class Directory(object):

    @classmethod
    def find_sub_path(cls, path):
        article_list = []

        temp_files = os.listdir(path)

        for temp_file in temp_files:
            # full path
            full_path = os.path.join(path, temp_file)

            # find .md
            if os.path.isfile(full_path) and os.path.splitext(full_path)[1] == ".md":
                article = Article(full_path)
                article_list.append(article)
            # find dir
            elif os.path.isdir(full_path):
                article_list.extend(cls.find_sub_path(full_path))

        return article_list


class XTDirectoryPicker(object):

    def __init__(self):
        # data
        self.download_error_list = []
        self.all_pic_count = 0
        self.current_pic_index = 0

        # ui
        self.root = Tk()
        self.root.title("XTImageDownloader")
        self.path = StringVar()
        self.title = StringVar()
        self.title.set("请选择Markdown文件所在文件夹")

        self.list_box = None
        Label(self.root, textvariable=self.title).grid(row=0, column=1)
        Label(self.root, text="文件夹路径:").grid(row=1, column=0)
        Entry(self.root, textvariable=self.path).grid(row=1, column=1)
        Button(self.root, text="选择路径", command=self.select_path).grid(row=1, column=2)
        self.root.mainloop()

    def select_path(self):
        self.path.set(tkFileDialog.askdirectory())
        if self.path.get() != "":
            Button(self.root, text="开始搜索并下载", command=self.start_search_dir).grid(row=2, column=1)
            return self.path

    def start_search_dir(self):
        self.all_pic_count = 0
        self.current_pic_index = 0
        self.download_error_list = []
        # get article list
        article_list = Directory.find_sub_path(self.path.get())

        # update ui
        for article in article_list:
            self.all_pic_count += len(article.pic_list)
        self.change_title(self.all_pic_count, self.current_pic_index);

        # download pic
        for article in article_list:
            for pic in article.pic_list:
                # start download pic
                thread = threading.Thread(target=pic.start_download_pic, args=(self.download_pic_callback,))
                thread.start()

    def download_pic_callback(self, pic):
        # save error
        if pic.error_reason is not None and len(pic.error_reason) > 0:
            self.download_error_list.append(pic)

        self.current_pic_index += 1

        # update ui
        print('finish:' + str(self.current_pic_index) + '/' + str(self.all_pic_count))
        self.change_title(self.all_pic_count, self.current_pic_index)

        # finish all download
        if self.all_pic_count == self.current_pic_index:
            self.print_error(self.download_error_list)

    def change_title(self, total_num, current_num):
        self.title.set("已完成" + str(current_num) + "/" + str(total_num))

    def print_error(self, download_error_list):
        # python log
        print("-----------------------------------")
        print("some pic download failure:")
        for pic in download_error_list:
            print("")
            print("name:" + pic.name)
            print("url:" + pic.url)
            print("error_reason:" + pic.error_reason)

        Label(self.root, text="部分图片下载失败:").grid(row=4, column=1)

        # GUI
        # listbox
        self.list_box = Listbox(self.root)
        for pic in download_error_list:
            self.list_box.insert(END, pic.url + pic.error_reason)
        self.list_box.grid(row=5, column=0, columnspan=3, sticky=W+E+N+S)

        # scrollbar
        scr1 = Scrollbar(self.root)
        self.list_box.configure(yscrollcommand=scr1.set)
        scr1['command'] = self.list_box.yview
        scr1.grid(row=5, column=4, sticky=W+E+N+S)
        # horizontal scrollbar
        scr2 = Scrollbar(self.root, orient='horizontal')
        self.list_box.configure(xscrollcommand=scr2.set)
        scr2['command'] = self.list_box.xview
        scr2.grid(row=6, column=0, columnspan=3, sticky=W+E+N+S)


dir_picker = XTDirectoryPicker()

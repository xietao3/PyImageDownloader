# Python 萌新 - 实现 Markdown 图片下载器


>简书支持打包下载所有文章功能，可以方便作者转移或保存。但是图片不支持自动下载，最近在学Python，便写了一个md图片下载器。

# 目标

本人 Python 新手，欢迎大佬指点。本文主要是对源码进行解读，期望实现以下目标：

1. 一键下载所有Markdown文件中的图片，并保存到本地。
2. 图片根据文章分类
3. 简单易用。

**先上最终效果:**

![下载过程](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e37ddcb0f?w=350&h=350&f=gif&s=4808535)

![下载完成](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e37ceb442?w=700&h=397&f=gif&s=4342048)


# 实现步骤

1. 搜索指定文件夹，找出文件夹及子文件包含的md文件。
2. 匹配出md文件中所有的图片。
3. 所有图片异步下载。
4. 下载报告与GUI。
5. Python 打包工具。

![准备开工](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e39911bca?w=200&h=200&f=gif&s=19134)

## 1. 搜索文件夹中md文件

首先我们要根据用户指定的文件夹，搜索出该文件夹及其子文件夹中包含的md文件，并将这些文件的绝对路径加到数组当中。

```
class Directory(object):

    @classmethod
    def find_sub_path(cls, path):
        # 初始化一个空的文章列表
        article_list = []
        # 获取该文件夹下的所以子文件
        temp_files = os.listdir(path)
        # 遍历子文件
        for temp_file in temp_files:
            # 拼接该文件绝对路径
            full_path = os.path.join(path, temp_file)

            # 匹配.md文件 
            if os.path.isfile(full_path) and os.path.splitext(full_path)[1] == ".md":
                # 如果是.md文件 加入文章列表
                article = Article(full_path)
                article_list.append(article)
            # 如果是文件夹 进行递归继续搜索
            elif os.path.isdir(full_path):
                # 将子文件夹中的文章列表拼接到上级目录的文章列表中
                article_list.extend(cls.find_sub_path(full_path))

        return article_list
```

## 2. 匹配出md文件中的图片

为每一篇文章新建一个存放该文章中图片的文件夹，然后利用正则匹配出该文章中的所以图片，并保存到图片数组中。

```
# 文章类

class Article(object):

    def __init__(self, path):
        # 文章的绝对路径
        self.article_path = path
        # 拼接文章图片下载后保存的路径
        self.article_pic_dir = path.replace(".md", "_Image")
        # 新建保存文章图片的文件夹
        self.mkdir_image_dir()
        # 开始搜索图片
        self.pic_list = self.find_pics(self.article_path)

    # 查找图片
    def find_pics(self, article_path):
        # 打开md文件
        f = open(article_path, 'r')
        content = f.read()
        pics = []

        # 匹配正则 match ![]()
        results = re.findall(r"!\[(.+?)\)", content)

        index = 0
        for result in results:
            temp_pic = result.split("](")
            # 将图片加入到图片数组当中
            if len(temp_pic) == 2:
                pic = Picture(temp_pic[0], temp_pic[1], self.article_pic_dir, index)
                pics.append(pic)
            index += 1
        f.close()
        return pics

    # 新建图片的保存文件夹
    def mkdir_image_dir(self):
        # 如果该文件夹不存在 则新建一个
        if not os.path.exists(self.article_pic_dir):
            os.mkdir(self.article_pic_dir)
```

## 3. 下载图片

简单地判断了图片是否有类型，拼接图片的保存路径与命名。检查图片是否重复下载，检查图片链接是否合法，下载并且保存图片，同时做了下载失败的处理和保存失败的处理，保存了下载失败的原因，以便后面生成报告。

```
# 图片类
class Picture(object):

    def __init__(self, name, url, dir_path, index):
        # 该图片顺序下标  用于设置默认图片名字
        self.index = index
        # 图片名
        self.name = name
        # 图片链接
        self.url = url
        # 图片保存路径
        self.dir_path = dir_path
        # 图片下载失败原因
        self.error_reason = None

    # 开始下载
    def start_download_pic(self, download_pic_callback):
        pic_path = self.build_pic_name()

        # 已存在则不重复下载
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
        # 下载失败
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
        # 保存失败
        except IOError, error:
            print(error)
            self.error_reason = str(error)
            download_pic_callback(self)
            return
        
        # 下载完成回调
        download_pic_callback(self)

    # 组装图片保存命名
    def build_pic_name(self):
        # 剪去图片链接后的参数
        pic_url = self.url.split("?")[0]
        
        # 获取图片格式后缀 如果没有 默认jpg
        urls = pic_url.split(".")
        if len(urls) > 1:
            pic_type = urls[len(urls)-1]
        else:
            pic_type = "jpg"

        # 组装图片命名
        if self.name is not None and len(self.name) > 0:
            pic_name = self.name + "." + pic_type
        else:
            pic_name = "no_name_" + str(self.index) + "." + pic_type
        
        pic_path = os.path.join(self.dir_path, pic_name)
        return pic_path
```

## 4. 下载报告与GUI

a. 本来 ``XTImageDownloader`` 和 ``GUI`` 应该分开，但是对 ``Tkinter`` 理解还有限，所以就直接写，方便调用。

这部分代码主要是 **选择文件夹** 和 **开始搜索并下载** 的 UI 及逻辑处理。

![选择文件夹](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e37dce3dd?w=800&h=464&f=gif&s=4525547)

```
class XTImageDownloader(object):

    def __init__(self):
        # 数据
        self.download_error_list = []
        self.all_pic_count = 0
        self.current_pic_index = 0
        self.thread_lock = threading.Lock()
        self.search_button = None
        # 图形界面相关
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

    # 选择文件夹
    def select_path(self):
        self.path.set(tkFileDialog.askdirectory())
        # 用户选中文件夹之后 显示下载按钮
        if self.path.get() != "":
            self.search_button = Button(self.root, text="开始搜索并下载", command=self.start_search_dir)
            self.search_button.grid(row=2, column=1)
            return self.path

    # 开始搜索文件夹 并且下载
    def start_search_dir(self):
        self.search_button['state'] = DISABLED
        self.search_button['text'] = "正在下载..."
        
        self.all_pic_count = 0
        self.current_pic_index = 0
        self.download_error_list = []
        # 获取Markdown文件列表
        article_list = Directory.find_sub_path(self.path.get())

        # 更新搜索进度 刷新UI
        for article in article_list:
            self.all_pic_count += len(article.pic_list)
        self.change_title(self.all_pic_count, self.current_pic_index)

        # 开始下载图片
        for article in article_list:
            for pic in article.pic_list:
                # 开启异步线程下载图片 并且传入下载完成的回调
                thread = threading.Thread(target=pic.start_download_pic, args=(self.download_pic_callback,))
                thread.start()
```



b. 开启异步线程下载图片，回调函数作为入参传入。

![下载图片](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e37ddcb0f?w=350&h=350&f=gif&s=4808535)

```
  // 异步下载
  thread = threading.Thread(target=pic.start_download_pic,   args=(self.download_pic_callback,))
  thread.start()
```

回调函数更新 UI 告知下载进度，由于开启了多线程，这里需要加锁，防止资源竞争。全部下载成功后生成报告。
```
    # 下载图片完成后的回调函数
    def download_pic_callback(self, pic):
        # 获取线程锁
        self.thread_lock.acquire()
        # 如果下载失败 则保存到失败列表
        if pic.error_reason is not None and len(pic.error_reason) > 0:
            self.download_error_list.append(pic)

        self.current_pic_index += 1

        # 更新下载进度 刷新UI
        print('finish:' + str(self.current_pic_index) + '/' + str(self.all_pic_count))
        self.change_title(self.all_pic_count, self.current_pic_index)

        # 全部下载成功 刷新UI 生成失败报告
        if self.all_pic_count == self.current_pic_index:
            self.search_button['text'] = "下载完成"
            self.print_error(self.download_error_list)

        # 释放锁
        self.thread_lock.release()

    # 更新下载进度 刷新UI
    def change_title(self, total_num, current_num):
        self.title.set("已完成" + str(current_num) + "/" + str(total_num))
```

c. 生成失败报告，利用 list_box 来展示错误列表，并且添加了滑块，可以滑动浏览。

```
    # 生成失败列表
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
        # 新建listbox
        self.list_box = Listbox(self.root)
        for pic in download_error_list:
            self.list_box.insert(END, pic.url + " -> " + pic.error_reason)
        self.list_box.grid(row=5, column=0, columnspan=3, sticky=W+E+N+S)

        # 垂直 scrollbar
        scr1 = Scrollbar(self.root)
        self.list_box.configure(yscrollcommand=scr1.set)
        scr1['command'] = self.list_box.yview
        scr1.grid(row=5, column=4, sticky=W+E+N+S)
        # 水平 scrollbar
        scr2 = Scrollbar(self.root, orient='horizontal')
        self.list_box.configure(xscrollcommand=scr2.set)
        scr2['command'] = self.list_box.xview
        scr2.grid(row=6, column=0, columnspan=3, sticky=W+E+N+S)
```


d. 最后贴上引用到的标准库(Python 2.7)：

1. ``#!/usr/bin/env python``和``# -*- coding:utf-8 -*-``这两行是为了支持中文。
2. ``os``和``os.path``用于系统及文件查找。
3. ``re`` 正则匹配。
4. ``urllib2``网络库，用于下载图片。
5. ``Tkinter``和``tkFileDialog``是 GUI 库。
6. ``threading``多线程库。
```
#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import os.path
import re
import urllib2
from Tkinter import *
import tkFileDialog
import threading
```

## 5. Python 打包工具

![最终效果](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e37ccb441?w=440&h=452&f=gif&s=1038378)


这部分主要是讲如何把 Python 脚本打包打包成可以在 Mac 上运行的应用。



### [PyInstaller](http://www.pyinstaller.org/)

[图片上传失败...(image-fd72fe-1516382674300)]

PyInstaller 是一个打包工具，可以帮助你打包 Python 脚本，生成应用。

安装 PyInstaller

```
$ pip install pyinstaller
```

打包后在``dist``文件夹中可找到可执行文件
```
$ pyinstaller yourprogram.py
```
生成 app
```
$ pyinstaller --onedir -y  main.spec
```

### [py2app](https://pypi.python.org/pypi/py2app/)

py2app 也是打包工具，这里只是简单介绍一下，想要深入了解详细内容可以自行搜索。


切换到你的工程目录下

```
$ cd ~/Desktop/yourprogram
```

生成 setup.py 文件
```
$ py2applet --make-setup yourprogram.py
```

生成你的应用

```
$ python setup.py py2app
```

### [DMG Canvas](http://www.araelium.com/dmgcanvas)

![DMGCanvas](https://user-gold-cdn.xitu.io/2018/1/20/1610f76e5fc72cac?w=140&h=140&f=jpeg&s=3987)

DMG Canvas 可以将 Mac 应用打包成 DMG 镜像文件，并且傻瓜式操作。

## 总结
刚开始只是写了很简单的一部分功能，后来慢慢完善，逐渐才有了现在的样子，在这个过程中学到了很多东西，包括 Python 中的 GUI 和多线程操作，如何生成应用程序。希望能对一部分人有所帮助。


**最后贴上[Demo](https://github.com/xietao3/PyImageDownloader)，本人 Python 2.7 环境下运行的， Python 3以上是无法运行的。**


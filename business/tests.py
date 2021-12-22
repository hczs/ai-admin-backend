import zipfile
import os
from zipfile import ZipFile

from django.test import TestCase

# Create your tests here.
import common.utils


def extract_without_folder(arc_name, full_item_name, folder):
    with ZipFile(arc_name) as zf:
        file_data = zf.read(full_item_name)
    with open(os.path.join(folder, os.path.basename(full_item_name)), "wb") as file_out:
        file_out.write(file_data)


if __name__ == '__main__':
    # my_file_path = 'D:\\upload\\raw_data\\me.zip'
    # zip_file = zipfile.ZipFile(my_file_path)
    # print(zip_file.infolist())
    # print(zip_file.namelist())
    # for every in zip_file.namelist():
    #     path, file_name = os.path.split(every)
    #     if file_name:
    #         extract_without_folder(my_file_path, every, 'E:\\me')
    # zip_file.close()
    print(common.utils.pybyte(49092226))

import os
 
def rename_files(path):
    for file in os.listdir(path):
        newname = file.replace('*', 'x')
        Olddir = os.path.join(path, file)
        Newdir = os.path.join(path, newname)
        os.rename(Olddir, Newdir)
        print(f"Renamed {file} to {newname}")

if __name__ == '__main__':
    path = "./"
    rename_files(path)
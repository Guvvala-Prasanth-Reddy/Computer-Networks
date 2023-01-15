
The main idea of implementing this project is to develop something similar to **Internet Download Manager** i.e disrupting the advantage of opening **paralled TCP connections over SSL** and making using of **HTTP range requests** to download a subpart of the file and cache the file.

Upon successful download of the subparts from the internet using parallel tcp connections the files are stitched back into one file.

The best way to evalute the file genuinity is to check the md5 sum of file i.e stiched back and the original file if they match the download is perfect and crystal clear.

**Inorder to run this project you need to execute makefile and compile the code and run the latest executable file  since the project is implemented using C Language**  

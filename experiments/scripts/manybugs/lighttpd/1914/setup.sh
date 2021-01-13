project_name=lighttpd
bug_id=1914
dir_name=$1/manybugs/$project_name/$bug_id
download_url=https://repairbenchmarks.cs.umass.edu/ManyBugs/scenarios/lighttpd-bug-1913-1914.tar.gz
current_dir=$PWD
mkdir -p $dir_name
cd $dir_name
wget $download_url
tar xfz lighttpd-bug-1913-1914.tar.gz
mv lighttpd-bug-1913-1914 src
cd src

# fix the test harness and the configuration script
sed -i "s#/root/mountpoint-genprog/genprog-many-bugs/lighttpd-bug-1913-1914#/data/manybugs/lighttpd/1914/src#g" test.sh
sed -i "s#/data/manybugs/lighttpd/1914/src/limit#timeout 5#g" test.sh
sed -i "s#/usr/bin/perl#perl#g" test.sh
sed -i 's#lt-\.\*#lt-\.\* \&\> /dev/null#g' test.sh

# fix an obnoxious bug in tests/core-request.t
sed -i 's#image.JPG#image.jpg#g' lighttpd/tests/core-request.t

# fix broken symlinks
cd lighttpd/tests/tmp/lighttpd/servers/www.example.org/pages
rm symlinked index.xhtml
ln -s expire symlinked
ln -s index.html index.xhtml

# fix broken test file
cp $current_dir/mod-cgi.t /data/manybugs/lighttpd/1914/src/lighttpd/tests/mod-cgi.t

# compile program
cd $dir_name/src/lighttpd
make clean
CC=wllvm CXX=wllvm++ ./configure CFLAGS='-g -O0' --enable-static --disable-shared --with-pcre=no
CC=wllvm CXX=wllvm++ make CFLAGS="-march=x86-64" -j32


#sed -i 's/fabs/fabs_trident/g' libtiff/tif_luv.c
#sed -i 's/fabs/fabs_trident/g' tools/tiff2ps.c
#git add  libtiff/tif_luv.c tools/tiff2ps.c
#git commit -m 'replace fabs with proxy function'
#make CC=$TRIDENT_CC -j32

#sed -i '118d;221d' libtiff/tif_jpeg.c
#sed -i '153d;2429d' libtiff/tif_ojpeg.c
#git add libtiff/tif_ojpeg.c libtiff/tif_jpeg.c
#git commit -m 'remove longjmp calls'


#make CFLAGS="-ltrident_proxy -L/concolic-repair/lib -g" -j32
#sed -i '358i }' tools/gif2tiff.c
#sed -i '353i { TRIDENT_OUTPUT("obs", "i32", count);\n if (count < 0) klee_abort();\n' tools/gif2tiff.c
#sed -i '352d' tools/gif2tiff.c
#sed -i '352i while ((count = getc(infile)) &&  count <= 255 && (__trident_choice("L65", "bool", (int[]){count, status}, (char*[]){"x", "y"}, 2, (int*[]){}, (char*[]){}, 0)) )' tools/gif2tiff.c
#sed -i '43i #ifndef TRIDENT_OUTPUT\n#define TRIDENT_OUTPUT(id, typestr, value) value\n#endif\n' tools/gif2tiff.c
#git add tools/gif2tiff.c
#git commit -m "instrument trident"

#cd $current_dir
#cp repair.conf $dir_name
#cp spec.smt2 $dir_name
#cp t1.smt2 $dir_name
#cp -rf components $dir_name
#cp -rf tests $dir_name

project_name=libtiff
bug_id=bugzilla-2633
dir_name=$1/extractfix/$project_name/$bug_id
project_url=https://github.com/vadz/libtiff.git
commit_id=f3069a5


current_dir=$PWD
mkdir -p $dir_name
cd $dir_name
git clone $project_url src
cd src
git checkout $commit_id


./autogen.sh
CC=wllvm CXX=wllvm++ ./configure --enable-static --disable-shared
CC=wllvm CXX=wllvm++ make -j32

sed -i 's/fabs/fabs_trident/g' libtiff/tif_luv.c
sed -i 's/fabs/fabs_trident/g' tools/tiff2ps.c
git add  libtiff/tif_luv.c tools/tiff2ps.c
git commit -m 'replace fabs with proxy function'

sed -i '118d;221d' libtiff/tif_jpeg.c
sed -i '153d;2463d' libtiff/tif_ojpeg.c
git add libtiff/tif_ojpeg.c libtiff/tif_jpeg.c
git commit -m 'remove longjmp calls'


make CFLAGS="-ltrident_proxy -L/concolic-repair/lib" -j32

sed -i '2900i TRIDENT_OUTPUT("obs", "i32", t2p->tiff_datasize - count - 2 );' tools/tiff2pdf.c
sed -i '2898d' tools/tiff2pdf.c
sed -i '2898i if(__trident_choice("L1634", "bool", (int[]){count}, (char*[]){"x"}, 1, (int*[]){}, (char*[]){}, 0)) {' tools/tiff2pdf.c
sed -i '36i #ifndef TRIDENT_OUTPUT\n#define TRIDENT_OUTPUT(id, typestr, value) value\n#endif\n' tools/tiff2pdf.c
git add tools/tiff2pdf.c
git commit -m "instrument trident"


cd $current_dir
cp repair.conf $dir_name
cp spec.smt2 $dir_name
cp t1.smt2 $dir_name
cp -rf components $dir_name
cp exploit.tif $dir_name

source venv/Scripts/activate

#put the directory containing input files here, the code will automatically detect valid files
input_directory=DataFiles/Inputs/OXB_Data/tiling/
# put the basename of the files you want to analyze here without file extensions
barcodes=(
    bc1012
    bc1020
)
# put the expected rAAV payload size for each input file here
payload_sizes=(
    1831
    1872
)
# Put the desired output directory into this variable
output_directory="test_output_directory/"

# Modify the below if you want to play with argument flags, things should run fine without changing it. "-g five" sets the variant classification to 5 groups.
mkdir -p $output_directory
vector_subparser="CodeFiles/parse_file.py"
for i in ${!barcodes[@]}; do
    input_file=${input_directory}${barcodes[$i]}.tile.zmw.counts
    if python3 $vector_subparser -i ${input_file} -o $output_directory -p ${payload_sizes[$i]} -g five; then
        printf "succesfully run $input_file with payload size ${payload_sizes[$i]}\n"
    else
        printf 'failure in vector subparsing\n'
    fi
done
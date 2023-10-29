#!/bin/bash

source_dir=../../source/verb_clustering
data_dir=../../data/verb_clustering

# settings=(all_3_0 all_3_1 all_3_2)
settings=(all_3_0)

pretrained_model_name=bert-base-uncased

# vec_types=(word mask)
vec_types=(mask)

# model_name=siamese_distance
# margins=(0.1 0.2 0.5 1.0)

model_name=triplet_distance
margins=(0.1 0.2 0.5 1.0)

# model_name=arcface_classification
# margins=(0.01 0.02 0.05 0.1)

run_numbers=(00 01 02 03)

device=cuda:3

for setting in ${settings[@]}; do
    for vec_type in ${vec_types[@]}; do
        for ((i = 0; i < ${#run_numbers[@]}; i++)); do
            run_number=${run_numbers[${i}]}
            margin=${margins[${i}]}

            d1=${setting}
            d2=${pretrained_model_name}/${model_name}/${vec_type}/${run_number}
            python ${source_dir}/train_model.py \
                --input_train_file ${data_dir}/dataset/${d1}/exemplars_train.jsonl \
                --input_dev_file ${data_dir}/dataset/${d1}/exemplars_dev.jsonl \
                --output_dir ${data_dir}/train_model/${d1}/${d2} \
                --pretrained_model_name ${pretrained_model_name} \
                --model_name ${model_name} \
                --vec_type ${vec_type} \
                --run_number ${run_number} \
                --normalization true \
                --device ${device} \
                --batch_size 32 \
                --learning_rate 1e-5 \
                --n_epochs 5 \
                --margin ${margin}
        done
    done
done

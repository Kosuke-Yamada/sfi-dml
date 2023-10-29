#!/bin/bash

source_dir=../../source/verb_clustering
data_dir=../../data/verb_clustering

# settings=(all_3_0 all_3_1 all_3_2)
settings=(all_3_2)

pretrained_model_name=bert-base-uncased
model_names=(vanilla softmax_classification adacos_classification)

# vec_types=(word mask wm)
# vec_types=(word mask)
vec_types=(wm)

run_numbers=(00)

clustering_name=twostep
clustering_method1=xmeans
clustering_method2=average

for setting in ${settings[@]}; do
    for model_name in ${model_names[@]}; do
        for vec_type in ${vec_types[@]}; do
            d1=${setting}/${pretrained_model_name}/${model_name}
            d2=${vec_type}/${clustering_name}/${clustering_method1}/${clustering_method2}
            python ${source_dir}/find_best_params.py \
                --input_dir ${data_dir}/embedding/${d1} \
                --output_dir ${data_dir}/find_best_params/${d1}/${d2} \
                --vec_type ${vec_type} \
                --run_numbers ${run_numbers[@]} \
                --clustering_name ${clustering_name} \
                --clustering_method1 ${clustering_method1} \
                --clustering_method2 ${clustering_method2}
        done
    done
done

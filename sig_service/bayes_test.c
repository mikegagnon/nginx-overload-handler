/**
 * Copyright 2012 HellaSec, LLC
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 * ==== tester for bayesian classifier ====
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include "bayes.h"

void print_model(bayes_feature *features) {
    bayes_feature *current, *tmp;
    int i = 0;
    HASH_ITER(hh, features, current, tmp) {
        printf("'%s', %f, %f\n", current->token, current->positive_prob, current->negative_prob);
        i++;
    }
}

void find(bayes_feature *features, char * str) {
    bayes_feature *current;
    current = find_feature(features, str);
    if (current != NULL) {
        printf("'%s' --> pb == %f, np == %f\n", current->token, current->positive_prob, current->negative_prob);
    } else {
        printf("no '%s'\n", str);
    }
}

int main(int argc, char *argv[]) {
    bayes_feature *features = NULL; //, *current;
    double apriori_positive = 0.5;

    if (argc != 3) {
        fprintf(stderr, "Error: missing filename or string to classify\n");
        exit(1);
    }

    int f = open(argv[1], O_RDONLY);
    if (f == -1) {
        fprintf(stderr, "Error: while opening %s: %s\n", argv[1], strerror(errno));
        exit(1);
    }

    int result = load_model(&features, f);
    if (result < 0) {
        fprintf(stderr, "Error loading model = %d\n", result);
        exit(1);
    }

    //print_model(features);

    ssize_t len = strlen(argv[2]);
    // overwrite '\0' with 1 to test classify's ability to handle non-null terminated strings
    argv[2][len]= 1;

    int classification = classify(features, apriori_positive, argv[2], &argv[2][len]);
    printf("%s\n", classification > 0 ? "positive" : "negative");

    return 0;
}


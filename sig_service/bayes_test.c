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

#include <stdio.h>
#include <errno.h>
#include "bayes.h"

void find(bayes_feature *features, char * str) {
    bayes_feature *current;
    current = find_feature(features, str);
    if (current != NULL) {
        printf("'%s' --> pb == %f, np == %f\n", current->token, current->positive_prob, current->negative_prob);
    } else {
        printf("no '%s'\n", str);
    }
}

void main(int argc, char *argv[]) {
    bayes_feature *features = NULL; //, *current;
    double apriori_positive = 0.5;

    if (argc != 3) {
        fprintf(stderr, "Error: missing filename or string to classify\n");
        exit(1);
    }

    FILE *f = fopen(argv[1], "r");
    if (f == NULL) {
        fprintf(stderr, "Error: while opening %s: %s\n", argv[1], strerror(errno));
        exit(1);
    }

    int result = load_model(&features, f);
    if (result <= 0) {
        fprintf(stderr, "Error loading model\n");
        exit(1);
    }
    bayes_feature *current, *tmp;

    int classification = classify(features, apriori_positive, argv[2]);
    printf("%s\n", classification > 0 ? "positive" : "negative");

}


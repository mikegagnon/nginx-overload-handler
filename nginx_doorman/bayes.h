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
 * ==== bayesian classifier for Doorman ====
 */

#include "uthash.h"

#define MAX_TOKEN_STR_LEN 128
#define MAX_MODEL_LINE_LEN 180
#define MAX_TOKENS  5000
#define MODEL_FILE_BUF_SIZE ((MAX_MODEL_LINE_LEN + 1) * MAX_TOKENS)

typedef struct {
    char token[MAX_TOKEN_STR_LEN];

    // the probability that a positive message contains token
    double positive_prob;

    // like negative_prob but for negative messages
    double negative_prob;

    // for hashtable
    UT_hash_handle hh;
} bayes_feature;

void delete_model(bayes_feature ** features);
bayes_feature *find_feature(bayes_feature *features, char *token);
void add_feature(bayes_feature **features, char *token, double positive_prob, double negative_prob);
int load_model(bayes_feature **features, int fd);

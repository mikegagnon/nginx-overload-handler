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
 * TODO: have sig service perform cross validation, and have load_model
 * read in the results.
 */

#include "uthash.h"
#include "bayes.h"
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

/**
 * clears feature hashtable and sets *features = NULL
 */
void delete_model(bayes_feature ** features) {
    bayes_feature *current, *tmp;

    HASH_ITER(hh, *features, current, tmp) {
        HASH_DEL(*features, current);
        free(current);
    }
    *features = NULL;
}

/**
 * If feature already exists, then does not add it
 */
void add_feature(bayes_feature **features, char *token, double positive_prob, double negative_prob) {
    bayes_feature *feature;

    feature = find_feature(*features, token);
    if (feature != NULL) {
        return;
    }

    feature = malloc(sizeof(bayes_feature));
    strncpy(feature->token, token, MAX_TOKEN_STR_LEN);
    feature->token[MAX_TOKEN_STR_LEN - 1] = '\0';
    feature->positive_prob = positive_prob;
    feature->negative_prob = negative_prob;

    HASH_ADD_STR(*features, token, feature);
}

bayes_feature *find_feature(bayes_feature *features, char *token) {
    bayes_feature *feature;
    char search_str[MAX_TOKEN_STR_LEN];
    strncpy(search_str, token, MAX_TOKEN_STR_LEN);
    search_str[MAX_TOKEN_STR_LEN - 1] = '\0';

    // TODO make sure it only has 60 or fewer chars
    HASH_FIND_STR(features, search_str, feature);
    return feature;
}

// err != 0 means error; all err values < -1
// WARNING: this func is not thoroughly tested; it likely contains subtle errors not detected
// by the regression test
char *get_tokens(char *buf, char **token, double * positive, double * negative, int *err) {
    *token = buf;
    char *pos = NULL;
    char *neg = NULL;
    char *endptr;
    *err = 0;

    // find pos and neg
    // convert all commas an newlines to nulls
    for(; buf != NULL; buf++) {
        if (*buf == ',') {
            *buf = '\0';
            if (pos == NULL) {
                pos = buf + 1;
            } else if (neg == NULL) {
                neg = buf + 1;
            } else {
                // too many commas
                *err = -2;
                return NULL;
            }
        }
        else if (*buf == '\n') {
            if (pos == NULL || neg == NULL) {
                // not enough commas
                *err = -3;
                return NULL;
            }
            // keep skipping newlines until you find a non-newline char
            for ( ; buf != NULL; buf++) {
                if (*buf == '\n') {
                    *buf = '\0';
                } else {
                    break;
                }
            }
            break;
        }
    }

    *positive = strtod(pos, &endptr);
    if (endptr == pos) {
        *err = -4;
        return NULL;
    }
    *negative = strtod(neg, &endptr);
    if (endptr == neg) {
        *err = -5;
        return NULL;
    }
    return buf;
}

/**
 * if *features is not NULL, then clears the previous model
 * loads in a model from model_str and sets *features to point to the
 * model.
 *
 * model_str is a list of consecutive lines (separated by newlines; blank lines ignored)
 * Each line must contain a max of (MAX_MODEL_LINE_LEN - 1) chars, not including
 * the newline. (I.e. the line (without \n) + the '\0' should be <=
 * MAX_MODEL_LINE_LEN chars). Otherwise the line is ignored.
 *
 * Each line has the format:
 * TOKEN,POSITIVE_PROB,NEGATIVE_PROB
 * where TOKEN is a sequence of characters (with no commas), and the others are
 * double values.
 * TOKEN should contain fewer than MAX_TOKEN_STR_LEN characters or it
 * will be truncated.
 * returns number of features read, or a negative number on error
 */
int load_model(bayes_feature **features, int fd) {
    char line[MAX_MODEL_LINE_LEN];
    char *result;
    int i;
    int newlines_found;
    int end_i;
    char *token_str;
    double positive, negative;
    char *end_str;
    int count = 0;
    char file_buf[MODEL_FILE_BUF_SIZE];
    char *buf;
    ssize_t next_line_i = 0;
    int err;

    delete_model(features);

    ssize_t bytes_read = read(fd, file_buf, MODEL_FILE_BUF_SIZE);
    if (bytes_read >= MODEL_FILE_BUF_SIZE) {
        return -1;
    }

    // make it a null terminated str for easier parsing
    file_buf[bytes_read] = '\0';
    buf = file_buf;
    while (*buf != '\0') {
        buf = get_tokens(buf, &token_str, &positive, &negative, &err);
        if (err != 0) {
            goto abort_load_model;
        }
        add_feature(features, token_str, positive, negative);
        count++;
    }

    if (close(fd) != 0) {
        err = -1;
        goto abort_load_model;
    }

    return count;

abort_load_model:
    close(fd);
    delete_model(features);
    return err;

}

/**
 * finds token in source and copies it into dest (a max of maxbytes are copied).
 * converted to lowercase
 * sets dest to empty string when done
 * returns pointer of beginning of next token
 */
char * get_token(char *source, char *dest, int max_bytes) {
    char c;
    int i = 0;
    int j = 0;

    // First, skip over nonvalid chars
    while (source[i] != '\0') {
        c = source[i];
        if ((c >= 'A' && c <= 'Z') ||
            (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') ||
            c == '%') {
            break;
        }
        i++;
    }

    // Then, read in the token
    while (source[i] != '\0' && j < max_bytes - 1) {
        c = source[i];
        if (c >= 'A' && c <= 'Z') {
            dest[j] = c - 'A' + 'a';
            j++;
        } else if (
            (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') ||
            c == '%') {
            dest[j] = c;
            j++;
        } else {
            break;
        }
        i++;
    }

    dest[j] = '\0';
    return &source[i];
}


/**
 * classified string according to features. apriori_positive is the a priori probability that
 * the string is positive.
 * returns  1 if classified as a positive
 * returns -1 if negative
 */
int classify(bayes_feature *features, double apriori_positive, char *string) {
    bayes_feature *feature;
    char token[MAX_TOKEN_STR_LEN];
    double positive = apriori_positive;
    double negative = 1.0 - apriori_positive;

    while(1) {
        string = get_token(string, token, MAX_TOKEN_STR_LEN);
        if (token[0] == '\0') {
            break;
        }
        feature = find_feature(features, token);
        if (feature != NULL) {
            positive *= feature->positive_prob;
            negative *= feature->negative_prob;
        }
    }

    return positive > negative ? 1 : -1;
}


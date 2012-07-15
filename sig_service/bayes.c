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
#include "bayes.h"
#include <string.h>
#include <stdio.h>
#include <errno.h>

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
 * returns number of features read, or -1 if error
 */
int load_model(bayes_feature **features, FILE *file) {
    char line[MAX_MODEL_LINE_LEN];
    char *result;
    int i;
    int newlines_found;
    int first_comma_i;
    int second_comma_i;
    int end_i;
    char *token_str, *pos_str, *neg_str;
    double positive, negative;
    char *end_str;
    int count = 0;

    delete_model(features);

    while (1) {
        // get a line from the file
        result = fgets(line, MAX_MODEL_LINE_LEN, file);
        if (result == NULL) {
            break;
        }
        else if (line[0] == '\n') {
            continue;
        }

        // make sure there is 1 newline
        newlines_found = 0;
        for (i = 0; i <= MAX_MODEL_LINE_LEN; i++) {
            if (line[i] == '\n') {
                newlines_found += 1;
            } else if (line[i] == '\0') {
                break;
            }
        }
        if (newlines_found != 1) {
            goto abort_load_model;
        }

        // find the two commas
        first_comma_i = 0;
        second_comma_i = 0;
        end_i = 0;
        for (i = 0; i <= MAX_MODEL_LINE_LEN; i++) {
            if (line[i] == ',') {
                if (first_comma_i == 0) {
                    first_comma_i = i;
                } else if (second_comma_i == 0) {
                    second_comma_i = i;
                } else {
                    // too many commas
                    goto abort_load_model;
                }
            } else if (line[i] == '\0') {
                if (end_i == 0) {
                    end_i = i;
                }
                break;
            } else if (line[i] == '\n') {
                if (end_i == 0) {
                    end_i = i;
                } else {
                    // too many newlines
                    goto abort_load_model;
                }
            }
        }
        // not enough commas
        if (first_comma_i == 0 || second_comma_i == 0) {
            goto abort_load_model;
        }

        // convert commads to null termianted strings, for easier parsing
        line[first_comma_i] = '\0';
        line[second_comma_i] = '\0';

        token_str = line;
        pos_str = &line[first_comma_i + 1];
        neg_str = &line[second_comma_i + 1];

        positive = strtod(pos_str, &end_str);
        if (end_str != &line[second_comma_i]) {
            goto abort_load_model;
        }
        negative = strtod(neg_str, &end_str);
        if (end_str != &line[end_i]) {
            goto abort_load_model;
        }


        add_feature(features, token_str, positive, negative);
        count++;
    }

    fclose(file);
    return count;

abort_load_model:
    fclose(file);
    delete_model(features);
    return -1;

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

/**** for testing *****/

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
    printf("%d\n", classification);

}


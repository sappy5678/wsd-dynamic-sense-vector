"""Evaluate label propagation on a development set.

Usage:
  debug_lp.py --algo=<algo> --sim=<func> --gamma=<val>

Options:
  -h --help     Show this screen.
  --algo=<algo> Choose the algorithm (propagate, spread, or nearest) [default: propagate]
  --sim=<func>  Choose the similarity function to test (either rbf or expander)
  --gamma=<val> Value of gamma for RBF function
"""

import os
from datetime import datetime 
from collections import defaultdict
from label_propagation import LabelPropagation, expander, RBF, NearestNeighbor,\
    LabelSpreading, NearestNeighborOfAverage
from docopt import docopt
from version import version


def score_lp(system_input, system_output, gold):
    answers = []
    lemma_pos2answers = defaultdict(list)

    for key, input_info in system_input.items():

        assert len(system_output[key]) == len(gold[key]), 'output: %s, gold: %s' % (len(system_output[key]),
                                                                                    len(gold[key]))

        print('processing', key)

        for index, input_instance in enumerate(input_info):
            #print(index, input_instance)

            if input_instance[0] is None:
                system_answer = system_output[key][index]
                gold_answer = gold[key][index][0]

                #print('system', system_answer, 'gold', gold_answer)
                correct = system_answer == gold_answer
                answers.append(correct)
                lemma_pos2answers[key].append(correct)

    accuracy = sum(answers) / len(answers)

    for lemma_pos, lemma_pos_answers in lemma_pos2answers.items():
        lemma_pos_acc = sum(lemma_pos_answers) / len(lemma_pos_answers)
        print(lemma_pos, len(lemma_pos_answers), lemma_pos_acc)

    print('total', accuracy)
 
if __name__ == '__main__':
    import pickle
    from copy import deepcopy
    arguments = docopt(__doc__)
    print(arguments)
    if arguments['--sim'] == 'expander':
        sim_func = expander
    elif arguments['--sim'] == 'rbf':
        sim_func = RBF(float(arguments['--gamma']))
    else:
        raise ValueError('Unknown similarity function: %s' %arguments['--sim'])

    model_path='/var/scratch/mcpostma/testing/model-google-65/model-google/lstm-wsd-gigaword-google'
    vocab_path='/var/scratch/mcpostma/wsd-dynamic-sense-vector/output/gigaword-lstm-wsd.index.pkl'
#     model_path='output/2017-11-24-e93fdb2/lstm-wsd-gigaword-h256p64-seed_12-best-model'
#     vocab_path='preprocessed-data/2017-11-24-a74bda6/gigaword-for-lstm-wsd.index.pkl'
    path_system='output/dev.lp'
    path_gold='output/dev.lp.gold'

    path_senses_output = os.path.join('output', version, 'debug_lp__algo-%s_sim-%s_gamma-%s.pkl' 
                                      %(arguments['--algo'], arguments['--sim'], arguments['--gamma']))
    print('Senses written to %s' %path_senses_output)
    system_input = pickle.load(open(path_system, 'rb'))
    gold = pickle.load(open(path_gold, 'rb'))
    
    old_system_input = deepcopy(system_input)

    assert os.path.exists(vocab_path) and os.path.exists(model_path + '.meta'), \
            'Please update the paths hard-coded in this file (for testing only)'
    import tensorflow as tf
    with tf.Session() as sess:
        if arguments['--algo'] in ('propagate', 'LabelPropagation'): 
            lp = LabelPropagation(sess, vocab_path, model_path, 1000, sim_func=sim_func)
        elif arguments['--algo'] in ('spread', 'LabelSpreading'):
            lp = LabelSpreading(sess, vocab_path, model_path, 1000, sim_func=sim_func)
        elif arguments['--algo'] in ('nearest', 'NearestNeighbor'):
            lp = NearestNeighbor(sess, vocab_path, model_path, 1000, sim_func=sim_func)
        elif arguments['--algo'] in ('average', 'NearestNeighborOfAverage'):
            lp = NearestNeighborOfAverage(sess, vocab_path, model_path, 1000, sim_func=sim_func)
        else:
            raise ValueError('Unknown algorithm: %s' %arguments['--algo'])
        system_output = lp.predict(system_input)
        with open(path_senses_output, 'wb') as outfile:
            pickle.dump(system_output, outfile)
        lp.print_stats()
        print('Finished predicting at %s' %datetime.now())

    # score output (if gold provided)
    score_lp(old_system_input, system_output, gold)

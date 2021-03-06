"""contains single use functions for cleaning up and seeding the database

Once the database is all set up (as it is now) there is no need for any
of these functions.
"""


from model import *
from sqlalchemy import func
from os import listdir
from server import app


def get_frequent_words():
    """returns a dictionary of all words in the database and their frequency"""

    poems = db.session.query(Poem.text).all()
    word_dict = {}
    punctuation = (u'.', u',', u'?', u'!', u':', u'-', u'--', u'(', u')',
                   u';', u'\n', u'\t')
    for poem in poems:
        text = poem[0]
        for punct in punctuation:
            if punct in text:
                text = text.replace(punct, " ")
        words = [w.strip().lower() for w in text.split(" ") if len(w) > 0]
        for word in words:
            word_dict[word] = word_dict.get(word, 0) + 1

    return word_dict


def get_top_words_list(word_dict):
    """given dict of word: freq, returns a list of 1000 most frequent words"""

    top_nums = sorted(word_dict.items(), key=lambda tupe: tupe[1], reverse=True)
    top_words = [word for word, occurance in top_nums[0:1000]]
    return top_words


def load_poems():
    """Seeds the database with poems from the Poem_Files folder"""

    poems = listdir("webscrape/Poem_Files")

    for poem in poems:
        Poem.parse(poem)


def delete_link_tables(delete_id):
    """given a poem_id, removes tables linking it to subject, term, and region"""

    poem_subs = (PoemSubject.query.filter(PoemSubject.poem_id
                                          == delete_id).all())
    for poem_sub in poem_subs:
        print """Deleting PS ID: {},
                 P: {}, S: {}""".format(poem_sub.ps_id,
                                        poem_sub.poem_id,
                                        poem_sub.subject_id)
        db.session.delete(poem_sub)

    poem_terms = PoemTerm.query.filter(PoemTerm.poem_id
                                       == delete_id).all()
    for poem_term in poem_terms:
        print """Deleting PT ID: {},
                 P: {}, T: {}""".format(poem_term.pt_id,
                                        poem_term.poem_id,
                                        poem_term.term_id)
        db.session.delete(poem_term)

    poem_regions = PoemRegion.query.filter(PoemRegion.poem_id
                                           == delete_id).all()
    for poem_reg in poem_regions:
        print """Deleting PR ID: {},
                 P: {}, R: {}""".format(poem_reg.pr_id,
                                        poem_reg.poem_id,
                                        poem_reg.region_id)
        db.session.delete(poem_reg)


def clean_database():
    """removes duplicate poems, provided they have the same information"""

    duplicates = (db.session.query(Poem.title, Poem.poet_id)
                            .group_by(Poem.title, Poem.poet_id)
                            .having(func.count(Poem.poem_id) > 1).all())
    for title, poet_id in duplicates:
        poems = Poem.query.filter(Poem.title == title,
                                  Poem.poet_id == poet_id).all()
        if len(poems) > 1:
            for i in range(0, (len(poems) - 1)):
                model = poems[-1]
                test = poems[i]
                model_id = model.poem_id
                model_title = model.title.encode("utf-8")
                print "USING POEM {} AS MODEL FOR {}".format(model_id,
                                                             model_title)
                if (model.text == test.text
                        and model.subjects == test.subjects
                        and model.terms == test.terms
                        and model.regions == test.regions):

                    delete_id = test.poem_id
                    print "deleting poem: {}".format(delete_id)

                    delete_link_tables(delete_id)

                    db.session.commit()
                    db.session.delete(test)
                else:
                    print "Poem {} is different!".format(test.poem_id)


def clean_list_text(fileread, filewrite):
    """given a file with a word on each line, writes formatted text to new file"""

    file1 = open(fileread).read()
    file2 = open(filewrite, "w")
    words = file1.split("\r")
    new_words = []
    replace = ("#", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    for word in words:
        word = word.lower()
        for rep in replace:
            word = word.replace(rep, " ")
        word = word.strip()
        word = "'" + word + "', "
        new_words.append(word)
    new_words = set(new_words)
    for word in new_words:
        file2.write(word)
    file2.close()


def seed_metrics(poem_ids):
    """used to add a metrics object for each poem in poem_ids"""

    print "{} metrics to add".format(len(poem_ids))
    i = 1
    for poem_id in poem_ids:
        metric = Metrics.get_metrics(poem_id)
        print metric.poem_id
        print "Number: {}".format(i)
        i += 1
        db.session.add(metric)
        db.session.commit()
        print "DONE\n"


def adjust_rhyme(start):
    """updates the self.rhyme score for all metrics objects

    Will not need to be used.
    """

    metrics = Metrics.query.all()
    print "{} METRICS TO UPDATE".format(len(metrics))
    i = start
    for metric in metrics[start:]:
        text = metric.poem.text
        lines = Metrics._get_clean_line_data(text)
        rhyme_score = Metrics._get_rhyme_score(lines)
        metric.rhyme = rhyme_score
        print "{}: new rhyme score {}".format(metric.poem_id, metric.rhyme)
        db.session.commit()
        print "{} complete".format(i)
        i += 1


def adjust_end_score():
    """updates the self.end_repeat score for all metrics objects

    Will not need to be used.
    """

    metrics = Metrics.query.all()
    print "{} METRICS TO UPDATE".format(len(metrics))
    i = 1
    for metric in metrics:
        text = metric.poem.text
        lines = Metrics._get_clean_line_data(text)
        end_score = Metrics._get_end_rep_score(lines)
        metric.end_repeat = end_score
        print "{}: new end score {}".format(metric.poem_id, metric.end_repeat)
        db.session.commit()
        print "{} complete".format(i)
        i += 1


def add_poem_subject():
    """sets the metric_id equal to the poem_id for all PoemSubject instances

    Will not need to be used again.
    """

    ps = PoemSubject.query.all()
    print "TOTAL TO DO: {}".format(len(ps))
    n = 0
    for i in ps:
        i.metric_id = i.poem_id
        n += 1
        db.session.commit()
        print "{} complete".format(n)


def add_poem_term():
    """sets the metric_id equal to the poem_id for all PoemTerm instances

    Will not need to be used again.
    """

    pt = PoemTerm.query.all()
    print "TOTAL TO DO: {}".format(len(pt))
    n = 0
    for i in pt:
        i.metric_id = i.poem_id
        n += 1
        db.session.commit()
        print "{} complete".format(n)


def add_poem_region():
    """sets the metric_id equal to the poem_id for all PoemRegion instances

    Will not need to be used again.
    """

    pr = PoemRegion.query.all()
    print "TOTAL TO DO: {}".format(len(pr))
    n = 0
    for i in pr:
        i.metric_id = i.poem_id
        n += 1
        db.session.commit()
        print "{} complete".format(n)

if __name__ == "__main__":

    connect_to_db(app)
    print "Connected to DB."

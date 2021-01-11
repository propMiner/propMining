import os
from datetime import datetime
from typing import List

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from nltk import ne_chunk, word_tokenize
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from scipy.sparse import csr_matrix
import re
import nltk
from nltk.corpus import stopwords

from reproduce.filereader import FileReader
from reproduce.model import Commit, Keyword
import yaml


def run() -> None:
    # init
    sc = ReproductionAndTraining()

    # this checks the commit information
    sc.check()

    # the following lets you test different classifiers (takes a long time!)

    # print("TF/IDF Token")
    # sc.classifier(pre_fn=sc.tokenize, feature_fn=sc.tf_idf, relevant_group=sc.relevant_commits,
    #               labels=["relevant" for i in range(len(sc.relevant_commits))],
    #               out_txt="filtered_commits.txt")
    # print("TF/IDF Stemming")
    # sc.classifier(pre_fn=sc.stem_text, feature_fn=sc.tf_idf, relevant_group=sc.relevant_commits,
    #               labels=["relevant" for i in range(len(sc.relevant_commits))],
    #               out_txt="filtered_commits.txt")
    # print("TF/IDF Lemmatization")
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.tf_idf, relevant_group=sc.relevant_commits,
    #               labels=["relevant" for i in range(len(sc.relevant_commits))],
    #               out_txt="filtered_commits.txt")
    #
    # print("Bag of Words Token")
    # sc.classifier(pre_fn=sc.tokenize, feature_fn=sc.bag_of_words, relevant_group=sc.relevant_commits,
    #               labels=["relevant" for i in range(len(sc.relevant_commits))],
    #               out_txt="filtered_commits.txt")
    # print("Bag of Words Stemming")
    # sc.classifier(pre_fn=sc.stem_text, feature_fn=sc.bag_of_words, relevant_group=sc.relevant_commits,
    #               labels=["relevant" for i in range(len(sc.relevant_commits))],
    #               out_txt="filtered_commits.txt")

    # This is the reproduction - see notes for what

    # Best known Classifier
    print("Bag of Words Lemmatization")
    return sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
                  relevant_group=sc.relevant_commits, labels=["relevant" for i in range(len(sc.relevant_commits))],
                  out_txt="filtered_commits.txt"), sc

    # This code attempts to classify the categories individually. Just shows you that it doesn't really work.
    # Feel free to uncomment and test yourself
    # print("Testing per Cat")
    # print("Performance")
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
    #               relevant_group=sc.performance, labels=["relevant" for i in range(len(sc.performance))], out_txt="performance_commits.txt")
    # print("Bandwidth")
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
    #               relevant_group=sc.band, labels=["relevant" for i in range(len(sc.band))], out_txt="band_commits.txt")
    # print("Framerate")
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
    #               relevant_group=sc.frame, labels=["relevant" for i in range(len(sc.frame))], out_txt="frame_commits.txt")
    # print("Memory")
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
    #               relevant_group=sc.memory, labels=["relevant" for i in range(len(sc.memory))], out_txt="memory_commits.txt")
    # print("One Classifier - all labels")
    # commits = []
    # labels = []
    # commits.extend(sc.performance)
    # labels.extend(["performance" for i in range(len(sc.performance))])
    # commits.extend(sc.band)
    # labels.extend(["band" for i in range(len(sc.band))])
    # commits.extend(sc.frame)
    # labels.extend(["frame" for i in range(len(sc.frame))])
    # commits.extend(sc.memory)
    # labels.extend(["memory" for i in range(len(sc.memory))])
    #
    # sc.classifier(pre_fn=sc.lemmatize_text, feature_fn=sc.bag_of_words,
    #               relevant_group=commits, labels=labels, out_txt="oneclassifier_torulethemall.txt")


class ReproductionAndTraining:
    """
    Checks the commit data and reproduces the filtering
    It also provides a classifier that can be used on commits.
    """

    # Files to be read
    f_all = os.getcwd() + "/data/raw/all_commits.txt"
    f_f_band = os.getcwd() + "/data/raw/filterband.txt"
    f_f_frame = os.getcwd() + "/data/raw/filterframe.txt"
    f_f_memory = os.getcwd() + "/data/raw/filtermem.txt"
    f_f_perf = os.getcwd() + "/data/raw/filterperf.txt"
    f_p_band_cache = os.getcwd() + "/data/processed/Categories/Band/cache.txt"
    f_p_band_redundancy = os.getcwd() + "/data/processed/Categories/Band/reduncancy.txt"
    f_p_band_throttling = os.getcwd() + "/data/processed/Categories/Band/throttling.txt"
    f_p_band_unknown = os.getcwd() + "/data/processed/Categories/Band/unknown.txt"
    f_p_frame_redundant = os.getcwd() + "/data/processed/Categories/Frame/redundant.txt"
    f_p_frame_threading = os.getcwd() + "/data/processed/Categories/Frame/Threading.txt"
    f_p_frame_unknown = os.getcwd() + "/data/processed/Categories/Frame/Unknown.txt"
    f_p_frame_visual = os.getcwd() + "/data/processed/Categories/Frame/Visual.txt"
    f_p_memory_assets = os.getcwd() + "/data/processed/Categories/Memory/Assests.txt"
    f_p_memory_fixleak = os.getcwd() + "/data/processed/Categories/Memory/FixLeak.txt"
    f_p_memory_lowmem = os.getcwd() + "/data/processed/Categories/Memory/LowMem.txt"
    f_p_memory_reducesizedata = os.getcwd() + "/data/processed/Categories/Memory/reduceSizeData.txt"
    f_p_memory_unknown = os.getcwd() + "/data/processed/Categories/Memory/Unknown.txt"
    f_p_perf_algorithm = os.getcwd() + "/data/processed/Categories/Perf/Algorithm.txt"
    f_p_perf_assets = os.getcwd() + "/data/processed/Categories/Perf/assets.txt"
    f_p_perf_caching = os.getcwd() + "/data/processed/Categories/Perf/caching.txt"
    f_p_perf_concurrency = os.getcwd() + "/data/processed/Categories/Perf/Concurrency.txt"
    f_p_perf_datastructure = os.getcwd() + "/data/processed/Categories/Perf/DataStructure.txt"
    f_p_perf_earlyreturn = os.getcwd() + "/data/processed/Categories/Perf/EarlyReturn.txt"
    f_p_perf_orderofoperations = os.getcwd() + "/data/processed/Categories/Perf/OrderOFOperations.txt"
    f_p_perf_parsing = os.getcwd() + "/data/processed/Categories/Perf/Parsing.txt"
    f_p_perf_redundancy = os.getcwd() + "/data/processed/Categories/Perf/redundancy.txt"
    f_p_perf_sqlquery = os.getcwd() + "/data/processed/Categories/Perf/SQLQuery.txt"
    f_p_perf_timeout = os.getcwd() + "/data/processed/Categories/Perf/TimeOut.txt"
    f_p_perf_unknown = os.getcwd() + "/data/processed/Categories/Perf/Unknown.txt"

    # keywords used for each type
    keywords_band = ["network", "bandwidth", "size", "download", "upload", "socket"]
    keywords_frame = ["jank", "frame", "respons", "lag"]  # excluded "hang"
    keywords_memory = ["memory", "leak", "size", "cache", "buffer", "space"]
    keywords_perf = ["effic", "speed", "time", "perform", "slow", "fast"]
    keywords = []
    keywords.extend(keywords_band)
    keywords.extend(keywords_frame)
    keywords.extend(keywords_memory)
    keywords.extend(keywords_perf)
    band = []
    frame = []
    memory = []
    performance = []

    # processing units
    fr = FileReader()

    def __init__(self) -> None:
        super().__init__()

        # init ntlk and skelearn
        nltk.download("punkt")
        nltk.download("stopwords")
        nltk.download("wordnet")
        nltk.download("averaged_perceptron_tagger")
        nltk.download("words")
        nltk.download("maxent_ne_chunker")
        nltk.download("vader_lexicon")
        self.stops = stopwords.words("english")
        self.count_vectorizer = CountVectorizer()
        self.tfdif_vectorizer = TfidfVectorizer()
        self.stemmer = nltk.PorterStemmer()
        self.lemmatizer = nltk.WordNetLemmatizer()

        band_cache = self.fr.parse(self.f_p_band_cache)
        self.band.extend(band_cache)
        band_redundancy = self.fr.parse(self.f_p_band_redundancy)
        self.band.extend(band_redundancy)
        band_throttling = self.fr.parse(self.f_p_band_throttling)
        self.band.extend(band_throttling)
        band_unknown = self.fr.parse(self.f_p_band_unknown)
        self.band.extend(band_unknown)
        self.check_duplicates("band", self.band)
        self.band = list(set(self.band))

        frame_redundant = self.fr.parse(self.f_p_frame_redundant)
        self.frame.extend(frame_redundant)
        frame_threading = self.fr.parse(self.f_p_frame_threading)
        self.frame.extend(frame_threading)
        frame_unknown = self.fr.parse(self.f_p_frame_unknown)
        self.frame.extend(frame_unknown)
        frame_visual = self.fr.parse(self.f_p_frame_visual)
        self.frame.extend(frame_visual)
        self.check_duplicates("frame", self.frame)
        self.frame = list(set(self.frame))

        memory_assets = self.fr.parse(self.f_p_memory_assets)
        self.memory.extend(memory_assets)
        memory_fixleak = self.fr.parse(self.f_p_memory_fixleak)
        self.memory.extend(memory_fixleak)
        memory_lowmem = self.fr.parse(self.f_p_memory_lowmem)
        self.memory.extend(memory_lowmem)
        memory_unknown = self.fr.parse(self.f_p_memory_unknown)
        self.memory.extend(memory_unknown)
        memory_reducesizedata = self.fr.parse(self.f_p_memory_reducesizedata)
        self.memory.extend(memory_reducesizedata)
        self.check_duplicates("memory", self.memory)
        self.memory = list(set(self.memory))

        performance_algorithm = self.fr.parse(self.f_p_perf_algorithm)
        self.performance.extend(performance_algorithm)
        performance_assets = self.fr.parse(self.f_p_perf_assets)
        self.performance.extend(performance_assets)
        performance_caching = self.fr.parse(self.f_p_perf_caching)
        self.performance.extend(performance_caching)
        performance_concurrency = self.fr.parse(self.f_p_perf_concurrency)
        self.performance.extend(performance_concurrency)
        performance_datastructure = self.fr.parse(self.f_p_perf_datastructure)
        self.performance.extend(performance_datastructure)
        performance_earlyreturn = self.fr.parse(self.f_p_perf_earlyreturn)
        self.performance.extend(performance_earlyreturn)
        performance_orderofoperations = self.fr.parse(self.f_p_perf_orderofoperations)
        self.performance.extend(performance_orderofoperations)
        performance_parsing = self.fr.parse(self.f_p_perf_parsing)
        self.performance.extend(performance_parsing)
        performance_redundancy = self.fr.parse(self.f_p_perf_redundancy)
        self.performance.extend(performance_redundancy)
        performance_sqlquery = self.fr.parse(self.f_p_perf_sqlquery)
        self.performance.extend(performance_sqlquery)
        performance_timeout = self.fr.parse(self.f_p_perf_timeout)
        self.performance.extend(performance_timeout)
        performance_unknown = self.fr.parse(self.f_p_perf_unknown)
        self.performance.extend(performance_unknown)
        self.check_duplicates("performance", self.performance)
        self.performance = list(set(self.performance))

        relevant_commits = []
        relevant_commits.extend(self.band)
        relevant_commits.extend(self.frame)
        relevant_commits.extend(self.memory)
        relevant_commits.extend(self.performance)
        # reduce duplicates
        self.relevant_commits = list(set(relevant_commits))

        self.f_band = self.fr.parse(self.f_f_band)
        self.f_band = list(set(self.f_band))
        self.f_frame = self.fr.parse(self.f_f_frame)
        self.f_frame = list(set(self.f_frame))
        self.f_memory = self.fr.parse(self.f_f_memory)
        self.f_perf = self.fr.parse(self.f_f_perf)

        self.filtered_commits = []
        self.filtered_commits.extend(self.f_band)
        self.filtered_commits.extend(self.f_frame)
        self.filtered_commits.extend(self.f_memory)
        self.filtered_commits.extend(self.f_perf)

        irrelevant_commits = [i for i in self.filtered_commits if i not in self.relevant_commits]
        self.irrelevant_commits = list(set(irrelevant_commits))

        self.all_commits = self.fr.parse(self.f_all)
        unknown_commits = [i for i in self.all_commits if
                           i not in self.relevant_commits and i not in self.irrelevant_commits]
        self.unknown_commits = list(set(unknown_commits))
        self.vocab = set()

    def classifier(self, pre_fn, feature_fn, relevant_group, labels, out_txt):
        """"
        Attempts to create a classifier based on the manually filtered texts
        For now let's just attempt to predict "relevant" or "not-relevant"
        """

        # You can test different algorithms by switching the text_clf and parameters around
        # WARNING! Grid-Search is very expensive.
        text_clf = RandomForestClassifier()
        # text_clf = MultinomialNB()
        # text_clf = SGDClassifier()
        parameters = {'bootstrap': [False],
                      'max_depth': [None],
                      'max_features': ['auto'],
                      'min_samples_leaf': [1],
                      'min_samples_split': [2],
                      'n_estimators': [300]
                      }
        classifier = GridSearchCV(text_clf, parameters, n_jobs=-1)

        # featurize
        print("Start: " + datetime.now().strftime("%H:%M:%S"))
        relevant_features = [" ".join(pre_fn(x.text)) for x in relevant_group]
        irrelevant_features = [" ".join(pre_fn(x.text)) for x in self.irrelevant_commits]
        unknown_features = [" ".join(pre_fn(x.text)) for x in self.unknown_commits]
        features = []
        features.extend(relevant_features)
        features.extend(irrelevant_features)
        features.extend(unknown_features)

        x = feature_fn(features)
        y = labels
        y.extend(["irrelevant" for i in range(len(irrelevant_features))])
        print("Featurized: " + datetime.now().strftime("%H:%M:%S"))

        x_sub = x[:len(relevant_features) + len(irrelevant_features)]
        x_unknown = x[len(relevant_features) + len(irrelevant_features):]
        # create sets
        x_train, x_test, y_train, y_test = train_test_split(x_sub, y, test_size=0.2, random_state=0)

        # train classifier
        classifier.fit(x_sub, y)
        print("Trained: " + datetime.now().strftime("%H:%M:%S"))


        self.predict(classifier, x_unknown, self.unknown_commits, out_txt)

        return classifier

    def predict(self, classifier, features_x, features: List[Commit], file):
        """
        Predicts a list of commits according to the given features and classifier
        :param classifier: to be used for prediction
        :param features_x: feature vector
        :param features: commits according to feature vector
        :param file: to print results to
        :return: nothing
        """

        f = open(file, "a")
        prediction = classifier.predict(features_x)
        i = 0
        print("Predicting " + str(len([x for x in prediction if x != "irrelevant"])) + " to be relevant " + file)
        while i < len(prediction):
            if prediction[i] != "irrelevant":
                commit = features[i]
                f.write("commit " + commit.cmt_hash + " " + prediction[i] + "\n")
                f.write("Author: " + commit.author + "\n")
                f.write("Date: " + commit.date + "\n")
                f.write("\n" + commit.text + "\n\n")
            i += 1

    def check(self) -> List[Commit]:  # pylint: disable=R0201
        """"
        Checks if all commits are mapping correctly from raw -> filtered -> manually evaluated
        """
        print("")
        print("----- Checking Commit subset validity -----")

        print("Loaded all " + str(len(self.all_commits)) + " Commits")

        # check Bandwith
        print("Loaded " + str(len(self.f_band)) + " Filtered Bandwith Commits")
        self.contains(self.all_commits, self.f_band)

        print("Loaded " + str(len(self.band)) + " Bandwith Commits")
        self.contains(self.f_band, self.band)

        # Check framerate
        print("Loaded " + str(len(self.f_frame)) + " Filtered Framerate Commits")
        self.contains(self.all_commits, self.f_frame)

        print("Loaded " + str(len(self.frame)) + " Framerate Commits")
        self.contains(self.f_frame, self.frame)

        # check memory
        print("Loaded " + str(len(self.f_memory)) + " Filtered Memory Commits")
        self.contains(self.all_commits, self.f_memory)

        print("Loaded " + str(len(self.memory)) + " Memory Commits")
        self.contains(self.f_memory, self.memory)

        # check performance
        print("Loaded " + str(len(self.f_perf)) + " Filtered Performance Commits")
        self.contains(self.all_commits, self.f_perf)

        print("Loaded " + str(len(self.performance)) + " Performance Commits")
        self.contains(self.f_perf, self.performance)

        print("----- Checking Overlaps validity -----")
        o_p_m = [i for i in self.performance if i in self.memory]
        o_p_b = [i for i in self.performance if i in self.band]
        o_p_j = [i for i in self.performance if i in self.frame]
        o_m_p = [i for i in self.memory if i in self.performance]
        o_m_b = [i for i in self.memory if i in self.band]
        o_m_j = [i for i in self.memory if i in self.frame]
        o_b_p = [i for i in self.band if i in self.performance]
        o_b_m = [i for i in self.band if i in self.memory]
        o_b_j = [i for i in self.band if i in self.frame]
        o_j_p = [i for i in self.frame if i in self.performance]
        o_j_m = [i for i in self.frame if i in self.memory]
        o_j_b = [i for i in self.frame if i in self.band]

        print("            Performance Memory Bandwith Jankiness")
        print("Performance " + str(len(self.performance)).ljust(12) + str(len(o_p_m)).ljust(7) + str(len(o_p_b)).ljust(
            9) + str(len(o_p_j)).ljust(8))
        print("Memory      " + str(len(o_m_p)).ljust(12) + str(len(self.memory)).ljust(7) + str(len(o_m_b)).ljust(
            9) + str(len(o_m_j)).ljust(8))
        print(
            "Bandwidth   " + str(len(o_b_p)).ljust(12) + str(len(o_b_m)).ljust(7) + str(len(self.band)).ljust(9) + str(
                len(o_b_j)).ljust(8))
        print("Jankiness   " + str(len(o_j_p)).ljust(12) + str(len(o_j_m)).ljust(7) + str(len(o_j_b)).ljust(9) + str(
            len(self.frame)).ljust(8))

        print("----- Checking Keyword validity -----")

        print("Relevant to Irrelevant to Unknown: " + str(len(self.relevant_commits)) + " / " + str(
            len(self.irrelevant_commits)) + " / " + str(len(self.unknown_commits)))

        # check that all commits correspond to a keyword
        print("The following commits do not correspond to any keyword:")
        for commit in self.relevant_commits:
            if not any(word in commit.text for word in self.keywords):
                print(commit.cmt_hash)

        print("")

        # check keyword efficiency
        self.keywords.append("optimi")
        self.keywords.append("storage")
        keydict = dict()
        for word in self.keywords:
            k = Keyword(word)
            keydict[word] = k

        sum = 0
        sizedict = dict()
        for size in range(0, len(self.keywords)):
            sizedict[size] = 0
        for commit in self.relevant_commits:
            match = ""
            cnt = 0;
            for keyword in self.keywords:
                if keyword in commit.text:
                    keydict[keyword].positive_true += 1
                    match += keyword + " "
                    cnt += 1
            # print(str(cnt) + " " + match)
            sizedict[cnt] += 1
            sum += cnt
        print("Average matched keywords: " + str(sum / len(self.relevant_commits)))
        print("Matches per keyword count: ")
        for k, v in sizedict.items():
            if (v > 0):
                print("  " + str(k) + " - " + str(v))
        for commit in self.irrelevant_commits:
            for keyword in self.keywords:
                if keyword in commit.text:
                    keydict[keyword].positive_false += 1

        for k, v in keydict.items():
            ratio = 100
            if (v.positive_false > 0):
                ratio = v.positive_true / v.positive_false
            print(v.keyword.ljust(10) + " p: " + str(v.positive_true).ljust(3) + " n: " + str(v.positive_false).ljust(
                3) + " u: " + str(v.unknown).ljust(4) + " r: " + str(ratio)[:3])

        # count word occurences to see where we get
        print("----- Tokens in commit ratios -----")
        word_dict = dict()
        for commit in self.relevant_commits:
            # exclude token occuring > once
            for token in set(self.tokenize(commit.text)):
                if token in word_dict:
                    word_dict[token] += 1
                else:
                    word_dict[token] = 1
        irrelevant_commits_tokenized = [self.tokenize(commit.text) for commit in self.irrelevant_commits]
        unknown_comits_tokenized = [self.tokenize(commit.text) for commit in self.unknown_commits]
        for k, v in sorted(word_dict.items(), key=lambda item: item[1], reverse=True):
            negative = 0
            unknown = 0
            ratio = 1000000
            ratio2 = 1000000
            for commit in irrelevant_commits_tokenized:
                if k in commit:
                    negative += 1
            for commit in unknown_comits_tokenized:
                if k in commit:
                    unknown += 1
            if (negative > 0):
                ratio = v / negative
            if (unknown > 0):
                ratio2 = v / unknown
            if ((ratio > 0.5 and unknown > 0) or (ratio2 > 0.5 and unknown > 0)) and k not in self.keywords:
                print(str(k).ljust(24) + " p: " + str(v).ljust(2) + " n: " + str(negative).ljust(3) + " u: " + str(
                    unknown).ljust(3) + " rn: " + str(ratio)[:3] + " ru: " + str(ratio2)[:3])

    def tokenize(self, text: str) -> List[str]:
        """"
        Tokenizes a text string
        :param text: string of words to be tokenized
        :return: list of tokens.
        """
        tokens = [word for word in word_tokenize(text.lower()) if word.isalpha()]
        tokens = list(re.findall(r"[A-Za-z]+", " ".join(tokens)))
        tokens = [word for word in tokens if word not in self.stops]
        return tokens

    def lemmatize_text(self, text: str) -> List[str]:
        """"
        Conducts lemmatization of given text
        :param text: Text to be tokenized and lemmatized
        :return: array of lemmatized tokens.
        """
        out = [self.lemmatizer.lemmatize(token) for token in self.tokenize(text)]
        self.vocab = self.vocab.union(out)
        return out

    def lemmatize_new_text(self, text):
        lemmatized = [self.lemmatizer.lemmatize(token) for token in self.tokenize(text)]
        out = []
        for lem in lemmatized:
            if lem in self.vocab:
                out.append(lem)
        return out
        
        

    def bag_of_words(self, docs: List[str]) -> List[List[int]]:
        """"
        Featurization via bag of words.
        :param docs: Documents (texts) to be BOWed.
        :return: Feature vector
        """
        return self.count_vectorizer.fit_transform(docs).toarray()

    def tf_idf(self, docs: List[str]) -> csr_matrix:
        """"
        Featurization via TF/IDF.
        :param docs: Documents (texts) to be featurized.
        :return: Feature vector
        """
        return self.tfdif_vectorizer.fit_transform(docs).toarray()

    def stem_text(self, text: str) -> List[str]:
        """"
        Conducts stemming of given text
        :param text: Text to be tokenized and stemmed
        :return: array of stemmed tokens.
        """
        return [self.stemmer.stem(token) for token in self.tokenize(text)]

    def check_duplicates(self, name, group: List[Commit]):
        """
        Checks a group of duplicates
        :param name: name of grop (for output)
        :param group: of commits
        :return: nothing
        """
        seen = set()
        not_uniq = set()
        for x in group:
            if x not in seen:
                seen.add(x)
            else:
                not_uniq.add(x)
        for val in not_uniq:
            print(name + " duplicate: " + val.cmt_hash)

    def contains(self, group: List[Commit], contained: List[Commit]):
        """
        Checks if the contained commits are really contained in group
        :param group: to check if contained is in
        :param contained: commits that should be in group
        :return: nothing. Console print if contained items NOT in group
        """
        if not all(e in group for e in contained):
            print("  does not check out")
            for i in contained:
                if not i in group:
                    print("  Failed: " + i.cmt_hash)






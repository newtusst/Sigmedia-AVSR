import tensorflow as tf
from .encoder import Seq2SeqEncoder, AttentiveEncoder
from .decoder_bimodal import Seq2SeqBimodalDecoder
from .decoder_unimodal import Seq2SeqUnimodalDecoder


class Seq2SeqModel(object):
    def __init__(self,
                 data_sequences,
                 mode,
                 hparams):

        # member variables
        self._video_data = data_sequences[0]
        self._audio_data = data_sequences[1]

        self._mode = mode
        self._hparams = hparams

        self._make_encoders()
        self._make_decoder()
        self._init_saver()

    def _make_encoders(self):
        if self._video_data is not None:
            with tf.variable_scope('video'):
                self._video_encoder = Seq2SeqEncoder(
                    data=self._video_data,
                    mode=self._mode,
                    hparams=self._hparams,
                    gpu_id=0 % self._hparams.num_gpus
                )
        else:
            self._video_encoder = None

        if self._audio_data is not None:
            with tf.variable_scope('audio'):
                # self._audio_encoder = Seq2SeqEncoder(
                #     data=self._audio_data,
                #     mode=self._mode,
                #     hparams=self._hparams,
                #     gpu_id=1 % self._hparams.num_gpus
                # )
                self._audio_encoder = AttentiveEncoder(
                    data=self._audio_data,
                    mode=self._mode,
                    hparams=self._hparams,
                    gpu_id=1 % self._hparams.num_gpus,
                    attended_memory=self._video_encoder.get_data().outputs,
                    attended_memory_length=self._video_data.inputs_length
                )
        else:
            self._audio_encoder = None

    def _make_decoder(self):

        labels = None
        labels_length = None
        video_len = None
        audio_len = None

        if self._video_encoder is not None:
            video_output = self._video_encoder.get_data()
            labels = self._video_data.labels
            labels_length = self._video_data.labels_length
            video_len = self._video_data.inputs_length
        else:
            video_output = None

        if self._audio_encoder is not None:
            audio_output = self._audio_encoder.get_data()
            labels = self._audio_data.labels
            labels_length = self._audio_data.labels_length
            audio_len = self._audio_data.inputs_length
        else:
            audio_output = None

        if labels is None or labels_length is None:
            raise Exception('labels are None')

        # self._decoder = Seq2SeqBimodalDecoder(
        #     video_output=video_output,
        #     audio_output=audio_output,
        #     video_features_len=video_len,
        #     audio_features_len=audio_len,
        #     labels=labels,
        #     labels_length=labels_length,
        #     mode=self._mode,
        #     hparams=self._hparams
        # )

        ###
        # here finetune the video memory

        # tuner = AVFusion(
        #     source_output=audio_output,
        #     source_memory_lengths=audio_len,
        #     attended_output=video_output,
        #     attention_memory_lengths=video_len,
        #     hparams=self._hparams,
        #     mode=self._mode,
        # )
        # tuner = AVFusion(
        #     source_output=video_output,
        #     source_memory_lengths=video_len,
        #     attended_output=audio_output,
        #     attention_memory_lengths=audio_len,
        #     hparams=self._hparams,
        #     mode=self._mode,
        #
        # )

        # tuned_output = tuner.get_tuned_data()

        ###

        self._decoder = Seq2SeqUnimodalDecoder(
            encoder_output=audio_output,
            encoder_features_len=audio_len,
            labels=labels,
            labels_length=labels_length,
            mode=self._mode,
            hparams=self._hparams
        )

        self.train_op = self._decoder.train_op if self._mode == 'train' else None
        self.batch_loss = self._decoder.batch_loss if self._mode == 'train' else None

    def extract_results(self):

        pass

    def _init_saver(self):
        self.saver = tf.train.Saver(max_to_keep=300)

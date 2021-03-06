from ..layer_operation import LayerOperation
import tensorflow as tf
import re

class op_tf_lrn(LayerOperation):
    _attributes = """[]"""  # TODO: TO BE DEPRECATED

    def compile_time_operation(self, learning_option, cluster):
        pass

    def run_time_operation(self, learning_option, cluster):
        """
        define local response normalization(LRN) operation for input tensor.
        outputs:
            output: LRN output
        """
        # get input
        input_ = self.get_input('input')
        indim = self.get_dimension('input')

        # get attr
        # optional field
        local_size = self.get_attr('local_size', default=5)
        alpha = float(self.get_attr('alpha', default=1.0))
        beta = float(self.get_attr('beta', default=0.75))
        bias = float(self.get_attr('bias', default=1.0))

        # get worker info: worker num, device type, device num
        device = self.get_attr('device')
        num = re.sub('[^0-9]', '', cluster.get('types')[device])
        type = cluster.get('types')[device].replace(str(num), '')

        # construct API
        def apiConstructor():
            lrn = tf.nn.local_response_normalization(input_, depth_radius=local_size,
                                                     bias=bias, alpha=alpha, beta=beta)
            # get output dimension
            outdim = list(lrn.get_shape()[i].value for i in xrange(len(lrn.get_shape())))

            # set output
            self.set_dimension('output', outdim)
            self.set_output('output', lrn)

            # set tf summary
            tf.summary.histogram(self.name, lrn)

        with tf.variable_scope(self.name):
            if learning_option.get("parallel", None) != "DP":
                with tf.device('/job:worker/task:{0}/{1}:{2}'.format(device, type, num)):
                    apiConstructor()
            else:
                apiConstructor()
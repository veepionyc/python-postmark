import sys
import unittest


from io import BytesIO

if sys.version_info[0] < 3:
    from urllib2 import HTTPError
else:
    from urllib.error import HTTPError

import mock

from postmark import (
    PMBatchMail, PMMail, PMMailInactiveRecipientException,
    PMMailUnprocessableEntityException, PMMailServerErrorException,
    PMMailMissingValueException
)

from django.conf import settings


class PMMailTests(unittest.TestCase):
    def test_406_error_inactive_recipient(self):
        json_payload = BytesIO()
        json_payload.write(b'{"Message": "", "ErrorCode": 406}')
        json_payload.seek(0)

        message = PMMail(sender='from@example.com', to='to@example.com',
            subject='Subject', text_body='Body', api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            422, '', {}, json_payload)):
            self.assertRaises(PMMailInactiveRecipientException, message.send)

    def test_422_error_unprocessable_entity(self):
        json_payload = BytesIO()
        json_payload.write(b'{"Message": "", "ErrorCode": 422}')
        json_payload.seek(0)

        message = PMMail(sender='from@example.com', to='to@example.com',
            subject='Subject', text_body='Body', api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            422, '', {}, json_payload)):
            self.assertRaises(PMMailUnprocessableEntityException, message.send)

    def test_500_error_server_error(self):
        message = PMMail(sender='from@example.com', to='to@example.com',
            subject='Subject', text_body='Body', api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            500, '', {}, None)):
            self.assertRaises(PMMailServerErrorException, message.send)

    def assert_missing_value_exception(self, message_func, error_message):
        with self.assertRaises(PMMailMissingValueException) as cm:
            message_func()
        self.assertEqual(error_message, cm.exception.parameter)

    def test_send_with_template(self):
        # Confirm send() still works as before send_with_template() was added
        message = PMMail(sender='from@example.com', to='to@example.com',
            subject='Subject', text_body='Body', api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            200, '', {}, None)):
            self.assertTrue(message.send)

        # No subject should raise exception when using send()
        message = PMMail(sender='from@example.com', to='to@example.com',
                         text_body='Body', api_key='test')
        self.assert_missing_value_exception(
            message.send,
            'Cannot send an e-mail without a subject'
        )

        # Test new _check_values()
        # Try sending with template without a template ID or template model
        for kwargs in [{'subject': 'Subject', 'text_body': 'Body'},
                       {'template_id': 1},
                       {'template_model': {'junk': 'more junk'}}]:
            message = PMMail(api_key='test', sender='from@example.com', to='to@example.com', **kwargs)
            self.assert_missing_value_exception(
                message.send_with_template,
                'Cannot send a template e-mail without a both template_id and template_model set'
            )

        # Both template_id and template_model are set, so send_with_template should work.
        message = PMMail(api_key='test', sender='from@example.com', to='to@example.com',
                         template_id=1, template_model={'junk': 'more junk'})
        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            200, '', {}, None)):
            self.assertTrue(message.send_with_template)

        # Setting a subject with a template should raise an error
        message = PMMail(api_key='test', sender='from@example.com', to='to@example.com',
                         template_id=1, template_model={'junk': 'more junk'}, subject='Subject')
        self.assert_missing_value_exception(
            message.send_with_template,
            'If using Postmark templates, do not set the subject value'
        )


class PMBatchMailTests(unittest.TestCase):
    def test_406_error_inactive_recipient(self):
        messages = [
            PMMail(
                sender='from@example.com', to='to@example.com', 
                subject='Subject', text_body='Body', api_key='test'
            ),
            PMMail(
                sender='from@example.com', to='to@example.com',
                subject='Subject', text_body='Body', api_key='test'
            ),
        ]

        json_payload = BytesIO()
        json_payload.write(b'{"Message": "", "ErrorCode": 406}')
        json_payload.seek(0)

        batch = PMBatchMail(messages=messages, api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            422, '', {}, json_payload)):
            self.assertRaises(PMMailInactiveRecipientException, batch.send)

    def test_422_error_unprocessable_entity(self):
        messages = [
            PMMail(
                sender='from@example.com', to='to@example.com',
                subject='Subject', text_body='Body', api_key='test'
            ),
            PMMail(
                sender='from@example.com', to='to@example.com',
                subject='Subject', text_body='Body', api_key='test'
            ),
        ]

        json_payload = BytesIO()
        json_payload.write(b'{"Message": "", "ErrorCode": 422}')
        json_payload.seek(0)

        batch = PMBatchMail(messages=messages, api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            422, '', {}, json_payload)):
            self.assertRaises(PMMailUnprocessableEntityException, batch.send)

    def test_500_error_server_error(self):
        messages = [
            PMMail(
                sender='from@example.com', to='to@example.com',
                subject='Subject', text_body='Body', api_key='test'
            ),
            PMMail(
                sender='from@example.com', to='to@example.com',
                subject='Subject', text_body='Body', api_key='test'
            ),
        ]

        batch = PMBatchMail(messages=messages, api_key='test')

        with mock.patch('postmark.core.urlopen', side_effect=HTTPError('',
            500, '', {}, None)):
            self.assertRaises(PMMailServerErrorException, batch.send)


if __name__ == '__main__':
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                }
            },
            INSTALLED_APPS=[
            ],
            MIDDLEWARE_CLASSES=[],
        )

    unittest.main()

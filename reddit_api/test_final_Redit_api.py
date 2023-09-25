import unittest
from unittest.mock import patch, MagicMock, call
from reddit_api_for_test import process_submission, send_message
import datetime


class TestRedditApi(unittest.TestCase):

    @patch('reddit_api_for_test.logging.info')
    @patch('reddit_api_for_test.datetime.datetime')
    def test_process_submission(self, mock_datetime, mock_info):
        submission = MagicMock()
        submission.title = "Test Submission"
        submission.author = MagicMock()
        submission.author.name = 'test_author'

        comment1 = MagicMock()
        comment1.author = MagicMock()
        comment1.author.name = 'comment_author1'

        comment2 = MagicMock()
        comment2.author = MagicMock()
        comment2.author.name = 'comment_author2'

        submission.comments.list.return_value = [comment1, comment2]

        timestamp = "2023-09-22 12:00:00"
        fixed_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        mock_datetime.now.return_value = fixed_datetime

        process_submission(submission, timestamp)

        def custom_info(msg):
            self.assertIn(
                msg,
                [
                    f'[{fixed_datetime}] Title: Test Submission',
                    f'[{fixed_datetime}] Author name: test_author',
                    f'[{fixed_datetime}] Comment author: comment_author1',
                    f'[{fixed_datetime}] Comment author: comment_author2',
                    f'[{fixed_datetime}] -----------------------------------------------------------------'
                ]
            )

        mock_info.side_effect = custom_info

    @patch('reddit_api_for_test.logging.info')
    @patch('reddit_api_for_test.reddit.redditor')
    @patch('reddit_api_for_test.datetime.datetime')
    def test_send_message(self, mock_datetime, mock_redditor, mock_info):
        username = 'test_user'
        redditor_instance = MagicMock()
        mock_redditor.return_value = redditor_instance

        timestamp = "2023-09-22 13:00:00"
        fixed_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        mock_datetime.now.return_value = fixed_datetime

        send_message(username)

        redditor_instance.message.assert_called_once_with(subject="Title", message="message")
        mock_info.assert_has_calls([
            call(f'[{fixed_datetime}] Message sent to user: test_user'),
            call("-----------------------------------------------------------------")
        ])


if __name__ == '__main__':
    unittest.main()

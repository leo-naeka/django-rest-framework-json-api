from __future__ import absolute_import

from django.utils import timezone

from rest_framework import serializers

from . import TestBase
from rest_framework_json_api.utils import format_relation_name
from example.models import Blog, Entry, Comment, Author
from rest_framework_json_api.relations import ResourceRelatedField


class TestResourceRelatedField(TestBase):

    def setUp(self):
        super(TestResourceRelatedField, self).setUp()
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        self.entry = Entry.objects.create(
            blog=self.blog,
            headline='headline',
            body_text='body_text',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        for i in range(1,6):
            name = 'some_author{}'.format(i)
            self.entry.authors.add(
                Author.objects.create(name=name, email='{}@example.org'.format(name))
            )

        self.comment = Comment.objects.create(
            entry=self.entry,
            body='testing one two three',
            author=Author.objects.first()
        )

    def test_data_in_correct_format_when_instantiated_with_blog_object(self):
        serializer = BlogFKSerializer(instance={'blog': self.blog})

        expected_data = {
            'type': format_relation_name('Blog'),
            'id': str(self.blog.id)
        }

        actual_data = serializer.data['blog']

        self.assertEqual(actual_data, expected_data)

    def test_data_in_correct_format_when_instantiated_with_entry_object(self):
        serializer = EntryFKSerializer(instance={'entry': self.entry})

        expected_data = {
            'type': format_relation_name('Entry'),
            'id': str(self.entry.id)
        }

        actual_data = serializer.data['entry']

        self.assertEqual(actual_data, expected_data)

    def test_deserialize_primitive_data_blog(self):
        serializer = BlogFKSerializer(data={
            'blog': {
                'type': format_relation_name('Blog'),
                'id': str(self.blog.id)
            }
        }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['blog'], self.blog)

    def test_validation_fails_for_wrong_type(self):
        serializer = BlogFKSerializer(data={
            'blog': {
                'type': 'Entries',
                'id': str(self.blog.id)
            }
        }
        )

        self.assertFalse(serializer.is_valid())

    def test_serialize_many_to_many_relation(self):
        serializer = EntryModelSerializer(instance=self.entry)

        type_string = format_relation_name('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        expected_data = [{'type': type_string, 'id': str(pk)} for pk in author_pks]

        self.assertEqual(
            serializer.data['authors'],
            expected_data
        )

    def test_deserialize_many_to_many_relation(self):
        type_string = format_relation_name('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        authors = [{'type': type_string, 'id': pk} for pk in author_pks]

        serializer = EntryModelSerializer(data={'authors': authors, 'comment_set': []})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['authors']), Author.objects.count())
        for author in serializer.validated_data['authors']:
            self.assertIsInstance(author, Author)

    def test_read_only(self):
        serializer = EntryModelSerializer(data={'authors': [], 'comment_set': [{'type': 'Comments', 'id': 2}]})
        serializer.is_valid(raise_exception=True)
        self.assertNotIn('comment_set', serializer.validated_data)


class BlogFKSerializer(serializers.Serializer):
    blog = ResourceRelatedField(queryset=Blog.objects)


class EntryFKSerializer(serializers.Serializer):
    entry = ResourceRelatedField(queryset=Entry.objects)


class EntryModelSerializer(serializers.ModelSerializer):
    authors = ResourceRelatedField(many=True, queryset=Author.objects)
    comment_set = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = Entry
        fields = ('authors', 'comment_set')

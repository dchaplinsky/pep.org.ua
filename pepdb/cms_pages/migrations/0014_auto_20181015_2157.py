# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-10-15 18:57
from __future__ import unicode_literals

import cms_pages.models
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields
import wagtail.wagtailembeds.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0019_delete_filter'),
        ('taggit', '0002_auto_20150616_2121'),
        ('wagtailcore', '0040_page_draft_title'),
        ('cms_pages', '0013_auto_20180618_0150'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('introduction', models.TextField(blank=True, help_text='Text to describe the page')),
                ('image', models.ForeignKey(blank=True, help_text='Landscape mode only; horizontal width between 1000px and 3000px.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image')),
            ],
            options={
                'abstract': False,
            },
            bases=(cms_pages.models.AbstractJinjaPage, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='BlogPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('introduction', models.TextField(blank=True, help_text='Text to describe the page')),
                ('body', wagtail.wagtailcore.fields.StreamField([(b'heading_block', wagtail.wagtailcore.blocks.StructBlock([(b'heading_text', wagtail.wagtailcore.blocks.CharBlock(classname='title', required=True)), (b'size', wagtail.wagtailcore.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), (b'paragraph_block', wagtail.wagtailcore.blocks.RichTextBlock(icon='fa-paragraph', template='blocks/paragraph_block.html')), (b'image_block', wagtail.wagtailcore.blocks.StructBlock([(b'image', wagtail.wagtailimages.blocks.ImageChooserBlock(required=True)), (b'caption', wagtail.wagtailcore.blocks.CharBlock(required=False)), (b'attribution', wagtail.wagtailcore.blocks.CharBlock(required=False))])), (b'block_quote', wagtail.wagtailcore.blocks.StructBlock([(b'text', wagtail.wagtailcore.blocks.TextBlock()), (b'attribute_name', wagtail.wagtailcore.blocks.CharBlock(blank=True, label='e.g. Mary Berry', required=False))])), (b'embed_block', wagtail.wagtailembeds.blocks.EmbedBlock(help_text='Insert an embed URL e.g https://www.youtube.com/embed/SGJFWirQ3ks', icon='fa-s15', template='blocks/embed_block.html'))], blank=True, verbose_name='Page body')),
                ('subtitle', models.CharField(blank=True, max_length=255)),
                ('date_published', models.DateField(blank=True, null=True, verbose_name='Date article published')),
                ('image', models.ForeignKey(blank=True, help_text='Landscape mode only; horizontal width between 1000px and 3000px.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image')),
            ],
            options={
                'abstract': False,
            },
            bases=(cms_pages.models.AbstractJinjaPage, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='BlogPageTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_items', to='cms_pages.BlogPage')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cms_pages_blogpagetag_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='blogpage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text='A comma-separated list of tags.', through='cms_pages.BlogPageTag', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
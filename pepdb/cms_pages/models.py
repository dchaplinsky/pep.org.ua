# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.html import mark_safe
from django.utils import translation

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import Tag, TaggedItemBase

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.whitelist import (
    attribute_rule, allow_without_attributes)
from wagtail.wagtailadmin.edit_handlers import (
    InlinePanel, FieldPanel, PageChooserPanel, MultiFieldPanel, StreamFieldPanel)

from wagtail.wagtailsearch import index
from wagtail.wagtailembeds.blocks import EmbedBlock
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailcore.blocks import (
    CharBlock, ChoiceBlock, RichTextBlock, StreamBlock, StructBlock, TextBlock,
)

from core.utils import TranslatedField
from core.models import Person, Article, Document


@hooks.register('construct_whitelister_element_rules')
def whitelister_element_rules():
    return {
        'u': allow_without_attributes,
        'table': attribute_rule({'cellspacing': True, 'cellpadding': True,
                                 'border': True}),
        'td': attribute_rule({'valign': True, 'style': True}),
        'tr': allow_without_attributes,
        'th': allow_without_attributes,
        'tbody': allow_without_attributes,
        'tfoot': allow_without_attributes,
        'thead': allow_without_attributes,
        'p': attribute_rule({'align': True}),
    }


class AbstractJinjaPage(object):
    @hooks.register('insert_editor_js')
    def editor_js():
        return mark_safe(
            """
            <script>
                registerHalloPlugin(
                  "halloformat", {
                  "formattings": {
                     "bold": true,
                     "italic": true,
                     "strikethrough": false,
                     "underline": true
                }});

                registerHalloPlugin("hallojustify", {});
            </script>
            """
        )

    @hooks.register('insert_editor_css')
    def editor_css():
        return mark_safe(
            '<link rel="stylesheet" href="' + settings.STATIC_URL +
            'css/font-awesome.min.css">' +
            '<link rel="stylesheet" href="' + settings.STATIC_URL +
            'css/fucking-icons.css">')

    def get_context(self, request, *args, **kwargs):
        return {
            'self': self,
            'page': self,
            'request': request,
        }

    def localized_url(self, locale):
        translation.activate(locale)
        url = self.url
        translation.deactivate()
        return url


class StaticPage(AbstractJinjaPage, Page):
    body = RichTextField(verbose_name="Текст сторінки")
    template = "cms_pages/static_page.jinja"

    title_en = models.CharField(
        default="", max_length=255)

    body_en = RichTextField(
        default="",
        verbose_name="[EN] Текст сторінки")

    translated_title = TranslatedField(
        'title',
        'title_en',
    )

    translated_body = TranslatedField(
        'body',
        'body_en',
    )

    class Meta:
        verbose_name = "Статична сторінка"


StaticPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('title_en', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('body_en', classname="full"),
]


class LinkFields(models.Model):
    caption = models.CharField(max_length=255, blank=True,
                               verbose_name="Заголовок")
    caption_en = models.CharField(max_length=255, blank=True,
                                  verbose_name="[EN] Заголовок")

    translated_caption = TranslatedField(
        'caption',
        'caption_en',
    )

    link_external = models.URLField("Зовнішнє посилання", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Або посилання на існуючу сторінку"
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Зображення"
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        else:
            return self.link_external

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
        FieldPanel('caption_en'),
        FieldPanel('link_external'),
        PageChooserPanel('link_page')
    ]

    class Meta:
        abstract = True


class HomePageTopMenuLink(Orderable, LinkFields):
    page = ParentalKey('cms_pages.HomePage', related_name='top_menu_links')


class HomePageBottomMenuLink(Orderable, LinkFields):
    page = ParentalKey('cms_pages.HomePage', related_name='bottom_menu_links')


class HomePage(AbstractJinjaPage, Page):
    template = "cms_pages/home.jinja"

    title_en = models.CharField(
        default="", max_length=255)

    subtitle = RichTextField(
        default="",
        verbose_name="[UA] Текст над пошуком")

    subtitle_en = RichTextField(
        default="",
        verbose_name="[EN] Текст над пошуком")

    body = RichTextField(
        default="",
        verbose_name="[UA] Текст під пошуком")

    body_en = RichTextField(
        default="",
        verbose_name="[EN] Текст під пошуком")

    credits = RichTextField(
        default="",
        verbose_name="[UA] Текст під статистикою")

    credits_en = RichTextField(
        default="",
        verbose_name="[EN] Текст під статистикою")

    eu_desc = RichTextField(
        default="",
        verbose_name="[UA] Текст про EU")

    eu_desc_en = RichTextField(
        default="",
        verbose_name="[EN] Текст про EU")

    tr_desc = RichTextField(
        default="",
        verbose_name="[UA] Текст про Thomson Reuters")

    tr_desc_en = RichTextField(
        default="",
        verbose_name="[EN] Текст про Thomson Reuters")

    footer = RichTextField(
        default="",
        verbose_name="[UA] Текст внизу кожної сторінки")

    footer_en = RichTextField(
        default="",
        verbose_name="[EN] Текст внизу кожної сторінки")

    translated_title = TranslatedField(
        'title',
        'title_en',
    )

    translated_subtitle = TranslatedField(
        'subtitle',
        'subtitle_en',
    )

    translated_body = TranslatedField(
        'body',
        'body_en',
    )

    translated_credits = TranslatedField(
        'credits',
        'credits_en',
    )

    translated_tr_desc = TranslatedField(
        'tr_desc',
        'tr_desc_en',
    )

    translated_eu_desc = TranslatedField(
        'eu_desc',
        'eu_desc_en',
    )

    translated_footer = TranslatedField(
        'footer',
        'footer_en',
    )

    class Meta:
        verbose_name = "Головна сторінка"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('title_en', classname="full title"),

        FieldPanel('subtitle', classname="full title"),
        FieldPanel('subtitle_en', classname="full title"),

        FieldPanel('body', classname="full"),
        FieldPanel('body_en', classname="full"),

        FieldPanel('credits', classname="full"),
        FieldPanel('credits_en', classname="full"),

        FieldPanel('eu_desc', classname="full"),
        FieldPanel('eu_desc_en', classname="full"),
        FieldPanel('tr_desc', classname="full"),
        FieldPanel('tr_desc_en', classname="full"),

        InlinePanel('top_menu_links', label="Меню зверху"),
        InlinePanel('bottom_menu_links', label="Меню знизу"),

        FieldPanel('footer', classname="full"),
        FieldPanel('footer_en', classname="full"),
    ]

    def get_context(self, request, *args, **kwargs):
        ctx = super(HomePage, self).get_context(request, *args, **kwargs)

        ctx["persons_total"] = Person.objects.count()
        ctx["blogs_total"] = Article.objects.filter(kind="b", publish=True).count()
        ctx["investigations_total"] = Article.objects.filter(kind="i", publish=True).count()
        ctx["registries_total"] = 9  # Say 9
        ctx["docs_total"] = Document.objects.filter(doc__isnull=False).count()
        ctx["persons_pep"] = Person.objects.filter(type_of_official=1).count()
        ctx["persons_related"] = Person.objects.exclude(
            type_of_official=1).count()
        return ctx


class ImageBlock(StructBlock):
    """
    Custom `StructBlock` for utilizing images with associated caption and
    attribution data
    """
    image = ImageChooserBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)

    class Meta:
        icon = 'image'
        template = "blocks/image_block.html"


class HeadingBlock(StructBlock):
    """
    Custom `StructBlock` that allows the user to select h2 - h4 sizes for headers
    """
    heading_text = CharBlock(classname="title", required=True)
    size = ChoiceBlock(choices=[
        ('', 'Select a header size'),
        ('h2', 'H2'),
        ('h3', 'H3'),
        ('h4', 'H4')
    ], blank=True, required=False)

    class Meta:
        icon = "title"
        template = "blocks/heading_block.html"


class BlockQuote(StructBlock):
    """
    Custom `StructBlock` that allows the user to attribute a quote to the author
    """
    text = TextBlock()
    attribute_name = CharBlock(
        blank=True, required=False, label='e.g. Mary Berry')

    class Meta:
        icon = "snippet"
        template = "blocks/blockquote.html"


class BaseStreamBlock(StreamBlock):
    """
    Define the custom blocks that `StreamField` will utilize
    """
    heading_block = HeadingBlock()
    paragraph_block = RichTextBlock(
        icon="doc-full",
        template="blocks/paragraph_block.html"
    )
    image_block = ImageBlock()
    block_quote = BlockQuote()
    embed_block = EmbedBlock(
        help_text='Insert an embed URL e.g https://www.youtube.com/embed/SGJFWirQ3ks',
        icon="fa-s15",
        template="blocks/embed_block.html")


class BlogPageTag(TaggedItemBase):
    """
    This model allows us to create a many-to-many relationship between
    the BlogPage object and tags. There's a longer guide on using it at
    http://docs.wagtail.io/en/latest/reference/pages/model_recipes.html#tagging
    """
    content_object = ParentalKey('BlogPage', related_name='tagged_items', on_delete=models.CASCADE)


class BlogPage(AbstractJinjaPage, Page):
    """
    A Blog Page
    """
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Landscape mode only; horizontal width between 1000px and 3000px.'
    )
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
    subtitle = models.CharField(blank=True, max_length=255)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    date_published = models.DateField(
        "Date article published", blank=True, null=True
        )

    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        FieldPanel('date_published'),
        FieldPanel('tags'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    @property
    def get_tags(self):
        """
        Similar to the authors function above we're returning all the tags that
        are related to the blog post into a list we can access on the template.
        We're additionally adding a URL to access BlogPage objects with that tag
        """
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/'+'/'.join(s.strip('/') for s in [
                self.get_parent().url,
                'tags',
                tag.slug
            ])
        return tags

    # Specifies parent to BlogPage as being BlogIndexPages
    parent_page_types = ['BlogIndexPage']

    # Specifies what content types can exist as children of BlogPage.
    # Empty list means that no child content types are allowed.
    subpage_types = []


class BlogIndexPage(AbstractJinjaPage, Page):
    """
    Index page for blogs.
    We need to alter the page model's context to return the child page objects,
    the BlogPage objects, so that it works as an index page
    RoutablePageMixin is used to allow for a custom sub-URL for the tag views
    defined above.
    """
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Landscape mode only; horizontal width between 1000px and 3000px.'
    )

    content_panels = Page.content_panels + [
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
    ]

    # Speficies that only BlogPage objects can live under this index page
    subpage_types = ['BlogPage']

    # Defines a method to access the children of the page (e.g. BlogPage
    # objects). On the demo site we use this on the HomePage
    def children(self):
        return self.get_children().specific().live()

    # Overrides the context to list all child items, that are live, by the
    # date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(BlogIndexPage, self).get_context(request)
        context['posts'] = BlogPage.objects.descendant_of(
            self).live().order_by(
            '-date_published')
        return context

    # # This defines a Custom view that utilizes Tags. This view will return all
    # # related BlogPages for a given Tag or redirect back to the BlogIndexPage.
    # # More information on RoutablePages is at
    # # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    # @route('^tags/$', name='tag_archive')
    # @route('^tags/([\w-]+)/$', name='tag_archive')
    # def tag_archive(self, request, tag=None):

    #     try:
    #         tag = Tag.objects.get(slug=tag)
    #     except Tag.DoesNotExist:
    #         if tag:
    #             msg = 'There are no blog posts tagged with "{}"'.format(tag)
    #             messages.add_message(request, messages.INFO, msg)
    #         return redirect(self.url)

    #     posts = self.get_posts(tag=tag)
    #     context = {
    #         'tag': tag,
    #         'posts': posts
    #     }
    #     return render(request, 'blog/blog_index_page.html', context)

    def serve_preview(self, request, mode_name):
        # Needed for previews to work
        return self.serve(request)

    # Returns the child BlogPage objects for this BlogPageIndex.
    # If a tag is used then it will filter the posts by tag.
    def get_posts(self, tag=None):
        posts = BlogPage.objects.live().descendant_of(self)
        if tag:
            posts = posts.filter(tags=tag)
        return posts

    # Returns the list of Tags for all child posts of this BlogPage.
    def get_child_tags(self):
        tags = []
        for post in self.get_posts():
            # Not tags.append() because we don't want a list of lists
            tags += post.get_tags
        tags = sorted(set(tags))
        return tags
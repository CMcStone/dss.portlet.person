# -*- coding: utf-8 -*-
import re
import logging
from Products.FacultyStaffDirectory.interfaces.person import IPerson

from ComputedAttribute import ComputedAttribute
from plone.app.portlets.browser import formhelper
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.vocabularies.catalog import CatalogSource
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from zope import schema
from plone.app.uuid.utils import uuidToObject
from zope.interface import implements
from zope.component import getUtility
from zope.formlib import form
from zExceptions import NotFound
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget


from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from dss.portlet.person import PloneMessageFactory as _

logger = logging.getLogger('dss.portlet.personbadge')


class IPersonBadgePortlet(IPortletDataProvider):
    """A portlet which renders predefined static HTML.

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """
    
    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of this portlet portlet"),
        constraint=re.compile("[^\s]").match,
        required=False)

    chosen = schema.Choice(
        title=_(u"Choose a person"),
        description=_(u"Choose the Person this portlet is about"),
        required=True,
        source=SearchableTextSourceBinder({'object_provides': IPerson.__identifier__},
                                                                   default_query='path:'))

    omit_border = schema.Bool(
        title=_(u"Omit portlet border"),
        description=_(u"Tick this box if you want to render the text above "
            "without the standard header, border or footer."),
        required=True,
        default=True)

    footer = schema.TextLine(
        title=_(u"Portlet footer"),
        description=_(u"Text to be shown in the footer"),
        required=False)

    more_url = schema.ASCIILine(
        title=_(u"Details link"),
        description=_(u"If given, the header and footer "
            "will link to this URL."),
        required=False)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IPersonBadgePortlet)

    header = _(u"title_person_badge_portlet", default=u"Person badge Portlet")
    omit_border = True
    footer = u""
    more_url = ''

    def __init__(self, header=u"", chosen=None, text=u"", omit_border=True, footer=u"",
                 more_url=''):
        self.header = header
        self.chosen = chosen
        self.omit_border = omit_border
        self.footer = footer
        self.more_url = more_url

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen. Here, we use the title that the user gave or
        static string if title not defined.
        """
        return self.header or _(u'portlet_person_badge', default=u"Person Badge Portlet")
    

class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('person_badge.pt')
    
    def css_class(self):
      """Generate a CSS class from the portlet header
      """
      header = self.data.header
      if header:
          normalizer = getUtility(IIDNormalizer)
          return "portlet-personbadge-%s" % normalizer.normalize(header)
      return "portlet-personbadge"
      
    def has_link(self):
      return bool(self.data.more_url)

    def has_footer(self):
      return bool(self.data.footer)
      
    def person(self):
        """
        Returns the Person object or None if it does not exist.
        """
        return uuidToObject(self.data.chosen)

    def transformed(self, mt='text/x-html-safe'):
      """Use the safe_html transform to protect text output. This also
      ensures that resolve UID links are transformed into real links.
      """
      orig = self.data.text
      context = aq_inner(self.context)
      if not isinstance(orig, unicode):
          # Apply a potentially lossy transformation, and hope we stored
          # utf-8 text. There were bugs in earlier versions of this portlet
          # which stored text directly as sent by the browser, which could
          # be any encoding in the world.
          orig = unicode(orig, 'utf-8', 'ignore')
          logger.warn("Person portlet at %s has stored non-unicode text. "
              "Assuming utf-8 encoding." % context.absolute_url())

      # Portal transforms needs encoded strings
      orig = orig.encode('utf-8')

      transformer = getToolByName(context, 'portal_transforms')
      data = transformer.convertTo(mt, orig,
                                   context=context, mimetype='text/html')
      result = data.getData()
      if result:
          if isinstance(result, str):
              return unicode(result, 'utf-8')
          return result
      return None
  

   
class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IPersonBadgePortlet)
    form_fields['chosen'].custom_widget = UberSelectionWidget
    label = _(u"title_add_person_badge_portlet", default=u"Add person badge portlet")
    description = _(u"person_badge_portlet",
        default=u"This portlet displays the person addresst. This form enables borders and footers.")

    def create(self, data):
        return Assignment(**data)
    

class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IPersonBadgePortlet)
    form_fields['chosen'].custom_widget = UberSelectionWidget
    label = _(u"title_edit_person_portlet", default=u"Edit person badge portlet")
    description = _(u"description_person_badge_portlet",
        default=u"This portlet displays information about a Person. This form enables borders and footers.")
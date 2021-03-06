from __future__ import with_statement
import os
from mako.template import Template
from mako.lookup import TemplateLookup
from markdown import markdown
from datetime import datetime
import util

class JEntry:
    def __init__(self, inpath):
        """Read the infile and populate the object"""

        # First patse the config and extract data from infile
        self.inpath = inpath
        self.config = util.parse_config('core.cfg')
        with open(inpath) as infh:
            raw_header, self.content = infh.read().split('\n---\n')

        # Parse the header and populate the context with this
        # information
        self.context = self.__update_context(util.parse_header(raw_header))

        # Get a template ready to write
        tfile = util.view_mapper.get(self.context.get('view', 'default'))
        tlookup = TemplateLookup(directories = ['.'],
                                 output_encoding='utf-8',
                                 encoding_errors='replace')
        self.template = Template(filename = os.path.join('design', tfile),
                                 lookup = tlookup)

    def __render(self, template = None, context = None):
        """Renders a page given template and context"""
        
        if template is None:
            template = self.template
        if context is None:
            context = self.context
        extensions = ['codehilite', 'html_tidy']
        self.context['html_content'] = markdown(self.content, extensions)
        return template.render(**context)

    def __update_header(self, context = None):
        """Updates file header with given context. Function has
        side-effects and returns exit status"""
        
        if context is None:
            context = self.context
        with open(self.inpath, 'w') as infh:
            
            # Write context information in header_table
            for key in util.header_table:
                if context.get(key, None):
                    infh.write(key + ': '
                                        + context[key].__str__() + '\n')

            # Finish header. Write back original content
            infh.write('---\n' + self.content)
            return True
        return False

    def __update_context(self, context = None):
        """Post processing: Given certain values in context,
        calculates others"""
        
        if context is None:
            context = self.context
            
        # permalink might already be in header, in which case we don't
        # want to change it
        title = context.get('title', 'No Title')
        context['permalink'] = context.get('permalink',
                                           util.build_slug(title))
        context['draft'] = context.get('draft', None);
        
        # If pubdate is None, util.build_tiemstamp_h will return the
        # string "[Unpublished]"
        pubdate = context.get('pubdate', None)
        context['pubdate_h'] = util.build_timestamp_h(pubdate)
        return context

    def __write_out(self, outpath):
        """Render page and write it to a file"""

        with open(outpath, 'w') as outfh:
            outfh.write(self.__render())
        return True

    def publish(self, context = None):
        """Sets published and pubdate, updates header and context
        appropriately, and renders the page"""
        
        if context is None:
            context = self.context

        if not context['pubdate']:
            context['pubdate'] = datetime.now().strftime(util.time_isofmt)
        context = self.__update_context(context)
        self.__update_header(context)
        self.__write_out(util.build_path(self.config['outdir'],
                                         self.context['permalink']))
        return True

class JIndex:
    def __init__(self, target_list):
        """Index builder"""

        self.config = util.parse_config('core.cfg')
        self.context = self.__update_context(target_list)
        tfile = util.view_mapper.get('index')
        tlookup = TemplateLookup(directories = ['.'],
                                 output_encoding='utf-8',
                                 encoding_errors='replace')
        self.template = Template(filename = os.path.join('design', tfile),
                                 lookup = tlookup)

    def __render(self, template = None, context = None):
        """Renders a page given template and context"""

        if template is None:
            template = self.template
        if context is None:
            context = self.context
        return template.render(**context)

    def __update_context(self, target_list = None):
        """Builds context from target_list"""

        entries = []
        context = {}
        for target in target_list:
            with open(os.path.join(self.config['indir'], target + '.txt'), 'r') as infh:
                raw_header, content = infh.read().split('\n---\n')
                header = util.parse_header(raw_header)
                title = header.get('title', 'No Title')
                extensions = ['codehilite', 'html_tidy']
                snip = header.get('snip', markdown(content, extensions)[:50] + ' ...')
                pubdate = header.get('pubdate', None)

                # Has a date it was published, isn't a draft and isn't a static page
                if pubdate and not (header.get('draft', None) or header.get('static', None)):
                    entries.append({'title': title,
                                    'permalink': header.get('permalink', util.build_slug(title)),
                                    'snip': snip,
                                    'pubdate': pubdate})
        entries.sort(cmp = (lambda x, y: -1 if x['pubdate'] > y['pubdate'] else 1))
        context['entries'] = entries
        context['permalink'] = 'index'
        context['title'] = 'Journal'
        return context

    def __write_out(self, outpath):
        """Render page and write it to a file"""

        with open(outpath, 'w') as outfh:
            outfh.write(self.__render())
        return True

    def publish(self, context = None):
        """Writes out index file after building appropriate context"""

        if context is None:
            context = self.context

        self.__write_out(util.build_path(self.config['outdir'],
                                         self.context['permalink']))
        return True

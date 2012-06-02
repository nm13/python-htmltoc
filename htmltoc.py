#!/usr/bin/python

import BeautifulSoup as bs # expect BeautifulSoup v.3 ; TODO: test with v.4 
import re

from exceptions import Exception, TypeError


# our exception class
class TocNotFound( Exception ):
    pass

## class EncodingMismatch( TypeError ):
##     """ not enough info to convert input html and toc_marker to same encoding or unicode """


RE_H = re.compile( 'h[1-6]', re.I )


def _h_level( tag ): 
    """ h1 .. h6 -> 1..6, provided the tag *is* a header """
    
    return int( tag.name[1:] )


def _make_soup( html, text_encoding = None ):  
    
    return bs.BeautifulSoup( html, fromEncoding = text_encoding )


def _find_headers( soup ):
    
    headers = soup( name=RE_H )
    return headers


# TODO: may be turn to a class, separating initialization 
def _set_header_ids( list_of_headers ) : 
    """ go through the list of headers and set the ids, if there's any missing """
    
    headers_found = [0] * 7 ; # [ ( 0, )  0, 0, 0,   0, 0, 0 ]
    
    template = "header_" + "_%d" * 6 ; #  'header__%d_%d_%d_%d_%d_%d' 
    
    for h in list_of_headers:
        
        n = _h_level( h )
        
        headers_found[ n ] += 1 
        
        if h.get( 'id' ) is None:
            h[ 'id' ] = template % headers_found[1:]
            
        
    

class _TocMaker:
    """ a helper class """
    
    """
    strategy: we go through a list of h-tags, 
    maintaining current header level and a set of unclosed lists (1-6);
    
    then, for a next tag, if it is the same level -- we add a 'li' tag ; 
    
    if it is deeper -- we open new list ( add '<ul>' ), 
    change the current level,
    and mark new header list level as 'opened' ; 
    we also add our tag to the list as well ;
    
    if the tag is less deep -- we change the current level,
    close lists marked as opened on the levels below,
    open a new list at this level _if it didn't exist_,
    then add the tag to the list
    
    when all the tags are over -- we close all the lists marked as 'open' -- 
    -- and we're done!
    """
    
    def reset( self ):
    
        ## self.contents_parts = [''] # we'll join() it later 
        self.contents_parts = [ ] # we'll join() it later 
        
        self.open_lists = [0] * 7 # we'll count from 1
        
        # self.header_level = 0 # didn't see any headers yet


    def __init__( self ):
        """  """
    
        ## self.reset()
        pass
        
    
    def add_header( self, header ):
        """ add the tag to the future contents """
        
        id = header['id'] # shouldn't be empty as we must have set it before 
        contents = ''.join(  [ unicode(e) for e in header.contents ]  )
        
        entry = u'<li><a href="#%s">%s</a></li>\n' % ( id, contents )
        
        self.contents_parts.append( entry )


    def list_opened_at_level( self, level ):
        
        return   (  self.open_lists[ level ] > 0  )
        
    def start_list( self, level ):
        
        self.contents_parts.append('<ul>')
        
        self.open_lists[ level ] += 1
        
    def close_sublists( self, below_level ):
        """  """
        
        for i in xrange(   len( self.open_lists )   ):  
            
            if i > below_level :
                n = self.open_lists[ i ]
                if n > 0: 
                    self.contents_parts.append( '</ul>' * n )
                self.open_lists[ i ] = 0
                
            
    def build_toc( self, headers_list ):
        
        self.reset() # .contents_parts[], .header_levels
        
        header_level = 0
        for header in headers_list:
            level = _h_level( header )
            
            """
            if level == header_lever : # btw: level > 0 ( always ) 
                self.add_header( header )
            elif level > header_level :
                self.start_list( level )
                header_level = level
                self.add_header( header )
            else: # level < header_level 
                self.close_sublists( level )
                self.start_list( level )
                self.add_header( header )
                header_level = level
            """

            if level == header_level : # btw: level > 0 ( always ) 
                pass
            elif level > header_level :
                self.start_list( level )
                header_level = level
            else: # level < header_level 
                self.close_sublists( level )
                if not self.list_opened_at_level( level ):
                    self.start_list( level )
                header_level = level
            
            # add the header
            self.add_header( header )
            
        # close the lists that are left open 
        self.close_sublists( header ) 
        
        return ''.join( self.contents_parts )


#
# the toc marker can be a pseudo-tag, like <toc />,
# or text, like "[toc]" ; let us distinguish between these two
#

TEXT_MARKER  = 1
TAG_MARKER   = 2
    
class _TocMarker:
    """ do the same thing for two different types of the toc marker """
    
    def __init__( self, marker_text ):
        """ a marker should be just a tag, '<toc/>', or a string without ones, like '[toc]'; 
             we could have accepted mixed strings ( and do just a pure textual replacement for the TOC ),
             but currently we work at the HTML-tree-level, what seems to be more robust ;
             besides, this allows us to make the tag form of the toc marker to accept options, e.g.
             '<toc name="Contents" />'
        """
        
        soup = bs.BeautifulSoup( marker_text )
        
        # default
        self.marker_type = TEXT_MARKER
        
        marker = soup.contents[0]
        if isinstance( marker, bs.Tag ):
            self.marker_type = TAG_MARKER
            self.marker_text = marker.name
        else:
            # assert isinstance( marker, bs.NavigableString ) # or isinstance( marker, unicode )
            self.marker_text = unicode( marker )
        
    def find_and_replace( self, toc_text, soup ):
        """ locate the first element containing the marker, 
            then replace it with the contents of the 'toc_text'; 
             
             nb. we do not need to build a full soup tree 
                 from the 'toc_text' code -- for the nonce,
                 it would be just enough to insert it as text
                 
            returns True or False depending on success of the operation.
        """
        
        # debug: if we have missed something 
        #        with the str <-> unicode conversion, 
        #        we'll probably catch it here 
        u_toc_text = unicode( toc_text )
        
        ret = True
        if self.marker_type == TAG_MARKER:
            
            toc_tag = soup.find( name = self.marker_text )
            
            if toc_tag is None : 
                ret = False # no marker found 
            else :
                # TODO: process tag attributes as arguments
                toc_tag.replaceWith( u_toc_text )
            
        else: # TEXT_MARKER
            
            # string_entry = soup.find( text = self.marker_text )
            string_entry = soup.find( text = lambda s: s.find(self.marker_text) >= 0 )
            
            if string_entry is None:
                ret = False # no marker found 
            else :
                # new_text = string_entry.replace( self.marker_text, u_toc_text, count = 1 )
                n_replacements = 1
                new_text = string_entry.replace( self.marker_text, u_toc_text, n_replacements )
                string_entry.replaceWith( new_text )
            
        return ret


def add_toc( html, toc_marker, encoding_hint = None ):
    """ generate a table of contents and put it at the location of the marker ;
        if no toc marker was found, raise an exception """
    
    soup = _make_soup( html, encoding_hint )
    # if encoding_hint is not None:

    # want arguments of compatible type, 
    # and let utf-8 be the default: 
    soup_encoding = soup.originalEncoding or 'utf8'
    
    if not isinstance( toc_marker, unicode ) :
        toc_marker = unicode( toc_marker, soup_encoding )
    
    headers = _find_headers( soup )
    # set the ids, if there are any missing
    _set_header_ids( headers )
    
    toc_code = _TocMaker().build_toc( headers )
    
    replaced = _TocMarker( toc_marker ).find_and_replace( toc_code, soup )
    if not replaced:
        raise TocNotFound(  u"marker '%s' was not found in the given text" % (toc_marker, )  )
    # else ... 

    # result = soup.toEncoding( ... )
    u_html = unicode( soup )
    if isinstance( html, unicode ):
        result = u_html
    else:
        result = u_html.encode( soup.originalEncoding, 'xmlcharrefreplace' )

    return result


if __name__ == '__main__' :
    
    import sys 
    
    infile = sys.stdin
    outfile = sys.stdout
    
    encoding_hint = None
    # toc_marker = None
    
    n_args = len( sys.argv ) - 1 
    
    if 3 == n_args:
        
        infile = open( sys.argv[1] )
        toc_marker = sys.argv[2]
        encoding_hint = sys.argv[3]

    elif 2 == n_args:
        
        infile = open( sys.argv[1] )
        toc_marker = sys.argv[2]
        
    elif 1 == n_args: 
        
        # infile = sys.stdin
        toc_marker = sys.argv[1]
        
    else: # no arguments or too many
        
        print >>sys.stderr, "usage:"
        print >>sys.stderr, "%s [filename] toc_marker [encoding]"
        
        sys.exit(1)
    
    
    html = infile.read()
    
    try:
        result = add_toc( html, toc_marker, encoding_hint )
        outfile.write( result )

    except TocNotFound, tnf :
        print >>sys.stderr, 'error:\n', tnf
        

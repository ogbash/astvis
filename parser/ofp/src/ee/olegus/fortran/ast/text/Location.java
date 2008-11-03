/**
 * 
 */
package ee.olegus.fortran.ast.text;

import org.antlr.runtime.Token;
import org.antlr.runtime.TokenStream;
import org.antlr.runtime.tree.CommonTree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.Statement;

/**
 * @author olegus
 *
 */
public class Location implements XMLGenerator {
	
	
	/**
	 * For XML generator. 
	 */
	public static ThreadLocal<TokenStream> tokenStream = new ThreadLocal<TokenStream>();
	
	public int start = -1;
	public int stop = -1;
	public Code code;
	public Statement statement;
	
	public Location(int start, int stop, Code code, Statement statement) {
		this.start = start;
		this.stop = stop;
		this.code = code;
		this.statement = statement;
	}

	public Location(CommonTree tree, Code code, Statement statement) {
		this(tree.startIndex==-1?tree.token.getTokenIndex():tree.startIndex,
				tree.stopIndex==-1?tree.token.getTokenIndex()+1:tree.stopIndex,
						code, statement);
	}

	public Location() {
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		handler.startElement("", "", "location", null);

		// begin
		attrs.clear();
		attrs.addAttribute("", "", "tokenIndex", "", ""+start);
		if(tokenStream!=null && start>=0) {
			attrs.addAttribute("", "", "line", "", ""+tokenStream.get().get(start).getLine());
			attrs.addAttribute("", "", "column", "", ""+tokenStream.get().get(start).getCharPositionInLine());
		}
		handler.startElement("", "", "begin", attrs);
		handler.endElement("", "", "begin");
		
		//end
		attrs.clear();
		attrs.addAttribute("", "", "tokenIndex", "", ""+stop);
		if(tokenStream!=null && stop>=0) {
			Token token = tokenStream.get().get(stop);
			attrs.addAttribute("", "", "line", "", ""+token.getLine());
			attrs.addAttribute("", "", "column", "", ""+
					(token.getCharPositionInLine() +token.getText().length()));
		}
		handler.startElement("", "", "end", attrs);
		handler.endElement("", "", "end");

		handler.endElement("", "", "location");
	}
	
	public String toString() {
		return start+":"+stop;
	}
}

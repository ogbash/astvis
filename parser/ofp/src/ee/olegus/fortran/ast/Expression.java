/**
 * 
 */
package ee.olegus.fortran.ast;

import org.antlr.runtime.tree.CommonTree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import ee.olegus.fortran.ASTVisitable;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * Super class of all expressions. Anything that evaluates to something.
 * 
 * @author olegus
 *
 */
public abstract class Expression implements TypeShape, Locatable, ASTVisitable, XMLGenerator {
	
	Location location;
	
	/**
	 * @deprecated parse with parser action
	 */
	public Expression(CommonTree tree, Code code, Statement statement) {
		location = new Location(tree, code, statement);
	}
	
	/**
	 * @deprecated parse with parser action
	 */
	public Expression(Location location) {
		this.location = location;
	}

	public Expression() {
	}

	public static Expression parse(CommonTree tree, Scope scope, Statement statement) {
		return new DataReference(tree, scope, statement);
	}

	public Location getLocation() {
		if(location == null) {
			location = new Location();
		}
		return location;
	}

	public void setLocation(Location location) {
		this.location = location;
	}
	
	public void generateXML(ContentHandler handler) throws SAXException {
		getLocation().generateXML(handler);			
	}	
}

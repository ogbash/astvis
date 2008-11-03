/**
 * 
 */
package ee.olegus.fortran.ast;

import org.antlr.runtime.tree.CommonTree;

import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class LocatableString implements CharSequence,Locatable {

	private String str;
	private Location location;
	
	
	public LocatableString(String str, CommonTree tree, Code code, Statement statement) {
		this.str = str;
		location = new Location(tree, code, statement);
	}
	
	public char charAt(int index) {
		return str.charAt(index);
	}

	public int length() {
		return str.length();
	}

	public CharSequence subSequence(int start, int end) {
		return str.subSequence(start, end);
	}

	public Location getLocation() {
		return location;
	}

	public String getString() {
		return str;
	}
	
	public String toString() {
		return getString();
	}
}

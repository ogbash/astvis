/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;

import ee.olegus.fortran.ast.text.Locatable;

/**
 * Variable, interface or other declaration.
 * 
 * @author olegus
 *
 */
public abstract class Declaration extends Statement implements Locatable {
	
	/**
	 * For intrinsic types.
	 */
	public Declaration() {
	}
	
	/** @deprecated */
	public Declaration(CommonTree tree, Code code, Statement statement) {
		//this.location = new Location(tree, code, statement);
	}

	/**
	 * @deprecated use parser action
	 */
	public static List<? extends Declaration> parseDeclarations(Tree tree, Code code) {
		List<Declaration> declarations = new ArrayList<Declaration>();
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			CommonTree child = (CommonTree) tree.getChild(i);
			switch(child.getType()) {
			case FortranParser.DECL:
				declarations.addAll(parseDeclaration(child, code));
				break;
			case FortranParser.T_INTERFACE:
				declarations.add(new Interface(child, code));
				break;
				
			case FortranParser.TYPE:
				Type type = new Type(child, code);
				declarations.add(type);
			}
		}*/
		return declarations;
	}
	
	/**
	 * @deprecated use parser action
	 */
	static private List<Variable> parseDeclaration(Tree tree, Code code) {
		List<Variable> variables = new ArrayList<Variable>();
		/*
		String type = tree.getChild(0).getText();
		Map<Attribute.Type,Attribute> attrs = null;
		for(int i=1; i<tree.getChildCount(); i++) {
			CommonTree child = (CommonTree) tree.getChild(i);
			switch(child.getType()) {
			case FortranParser.ATTRS:
				attrs = Attribute.parseAttributes(child);
				break;
			case FortranParser.T_IDENT:
				// TODO define one dummy statement for all declarations
				Variable v = new Variable(child, code, null, type, attrs);
				variables.add(v);
				break;
			}
		}*/
		return variables;
	}
}

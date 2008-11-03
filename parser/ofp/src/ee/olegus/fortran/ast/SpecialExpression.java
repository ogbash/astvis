/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;


/**
 * Asterisk or any other special symbol.
 * 
 * @author olegus
 *
 */
public class SpecialExpression extends Expression {

	public enum Symbol {
		ASTERISK,
		COLON
	}
	
	private Symbol symbol;
	
	public SpecialExpression(Symbol symbol) {
		this.symbol = symbol;
	}

	public Symbol getSymbol() {
		return symbol;
	}

	public void setSymbol(Symbol symbol) {
		this.symbol = symbol;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		// TODO Auto-generated method stub
		return 0;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getType() {
		// TODO Auto-generated method stub
		return null;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		// TODO Auto-generated method stub
		return false;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

}

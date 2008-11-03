package ee.olegus.fortran.ast;

import org.antlr.runtime.tree.CommonTree;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.XMLGenerator;


public class ProgramUnit extends Code implements Scope,WithinScope,XMLGenerator {
	public enum UnitType {
		PROGRAM,
		EXTERNAL_SUBPROGRAM,
		MODULE,
		BLOCK
	}

	private UnitType unitType;
	private String name;
	private String filename;
	
	
	/**
	 * @deprecated most parsing functionality goes to parser action
	 */
	public ProgramUnit(CommonTree tree, Scope scope) {
		super(tree, scope);
		/*
		filename = scope.getFilename();

		if(tree.getType()==FortranParser.T_MODULE)
			this.unitType = ProgramUnit.UnitType.MODULE;
		else if(tree.getType()==FortranParser.T_PROGRAM)
			this.unitType = ProgramUnit.UnitType.PROGRAM;
		
		this.name = tree.getChild(0).getText();
		
		parseProgramUnit();*/
	}

	public ProgramUnit() {
	}

	/**
	 * @deprecated parse with parser action
	 */
	private void parseProgramUnit() { // name <code element>*
		for(int i=1; i<getTree().getChildCount(); i++) {
			CommonTree child = (CommonTree) getTree().getChild(i);
		
			parseCodeElement(child);
		}
	}	
	
	@Override
	public boolean equals(Object obj) {
		return new EqualsBuilder()
			.append(name, name)
			.isEquals();
	}

	@Override
	public int hashCode() {
		return new HashCodeBuilder()
			.append(name)
			.toHashCode();
	}

	@Override
	public String toString() {
		StringBuffer str = new StringBuffer();
		str.append(unitType+" "+name+"\n");

		str.append(super.toString());
		
		return str.toString();
	}

	public String getName() {
		return name;
	}

	public String getFullName() {
		return getName();
	}

	public String getFilename() {
		return filename;
	}

	public UnitType getUnitType() {
		return unitType;
	}

	public void setFilename(String filename) {
		this.filename = filename;
	}

	public void setName(String name) {
		this.name = name;
	}

	public void setUnitType(UnitType unitType) {
		this.unitType = unitType;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		if(name != null)
			attrs.addAttribute("", "", "id", "", name);
		
		handler.startElement("", "", unitType.name().toLowerCase(), attrs);
		
		getLocation().generateXML(handler);
		
		super.generateXML(handler);
		
		handler.endElement("", "", unitType.name().toLowerCase());
	}
}

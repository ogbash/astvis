/**
 * 
 */
package ee.olegus.cpr;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Set;

import org.antlr.stringtemplate.StringTemplate;
import org.antlr.stringtemplate.StringTemplateGroup;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;

import ee.olegus.fortran.Parser;
import ee.olegus.fortran.ast.Attribute;
import ee.olegus.fortran.ast.Call;
import ee.olegus.fortran.ast.Callable;
import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.Executable;
import ee.olegus.fortran.ast.Expression;
import ee.olegus.fortran.ast.FunctionCall;
import ee.olegus.fortran.ast.ProgramUnit;
import ee.olegus.fortran.ast.Reference;
import ee.olegus.fortran.ast.Statement;
import ee.olegus.fortran.ast.Subprogram;
import ee.olegus.fortran.ast.SubroutineCall;
import ee.olegus.fortran.ast.TypeShape;
import ee.olegus.fortran.ast.Variable;
import ee.olegus.fortran.ast.cpr.PotentialCheckpoint;
import ee.olegus.fortran.ast.text.Locatable;

/**
 * @author olegus
 *
 */
@SuppressWarnings("static-access")
public class Analyzer {
	private static final Logger LOG = LogManager.getLogger(Analyzer.class);

	private Parser parser;
	
	private Map<Callable, References> references = new HashMap<Callable, References>();
	/** Locations that need checkpointing code around them. */
	private Map<Code,List<Locatable>> locatables;
	/** Locations that has been processed and checkpoint code generated. */
	private Map<Code,List<Locatable>> processedLocatables = new HashMap<Code, List<Locatable>>();
	/** Files that need to be created from templates.*/
	private Map<String, StringTemplate> stringTemplates = new HashMap<String, StringTemplate>();
	private Collection<SubroutineCall> mpiCalls = new ArrayList<SubroutineCall>();

	public Analyzer(Parser parser) {
		this.parser = parser;
	}

	public Map<String, StringTemplate> getStringTemplates() {
		return stringTemplates;
	}

	/**
	 * Find places that need to be refactored for checkpointing.
	 */
	public void analyze() {
		analyzeLocatables();
		analyzeMpiCalls();
	}

	static final Set<String> mpiNames = new HashSet<String>(Arrays.asList(new String[]{
		"mpi_init", "mpi_finalize",
		"mpi_send", "mpi_recv", "mpi_isend", "mpi_irecv", "mpi_wait",
		"mpi_reduce", "mpi_allreduce"
		}));

	/**
	 * Find all mpi calls
	 */
	private void analyzeMpiCalls() {
		
		for(Iterator<Code> codeIterator = parser.codeIterator(); codeIterator.hasNext(); ) {
			Code code = codeIterator.next();
			for(Statement statement: code.getConstructs()) {
				if(statement instanceof SubroutineCall) {
					SubroutineCall call = (SubroutineCall) statement;
					String name = call.getName();
					if(mpiNames.contains(name.toLowerCase())) {
						System.out.println("MPI: "+call.getName());
						mpiCalls.add(call);
					}
				}
			}
		}
	}

	/**
	 *  Find and store all potential checkpoints and function/procedure calls that
	 *  should be adviced (insert code around) with checkpoint code.
	 */
	private void analyzeLocatables() {
		locatables = new HashMap<Code,List<Locatable>>();
		Collection<PotentialCheckpoint> pcs = parser.getPotentialCheckpoints();
		
		Queue<Locatable> unprocessedLocatables = new LinkedList<Locatable>();
		
		for (PotentialCheckpoint pc: pcs) {
			unprocessedLocatables.add(pc); // add checkpoint itself
		}
		
		while(!unprocessedLocatables.isEmpty()) {
			Locatable locatable = unprocessedLocatables.poll();
			Code code = locatable.getLocation().code;
			List<Locatable> listForCode = locatables.get(code);
			if(listForCode == null) {
				listForCode = new ArrayList<Locatable>(3);
				locatables.put(code, listForCode);
			}
			
			listForCode.add(locatable);
			// find all calls to it
			if(locatable.getLocation().code instanceof Callable) {
				Callable callable = (Callable) locatable.getLocation().code;
				References references = this.references.get(callable);
				if(references != null) { // add all references
					for(Call call: references.getCalls()) {
						if(call instanceof Locatable && !contains(locatables, (Locatable)call)
								&& !unprocessedLocatables.contains(call)) {
							unprocessedLocatables.add((Locatable) call);
						}
					}
				}
			}
		}
	}
	
	private boolean contains(Map<Code, List<Locatable>> searchLocatables, Locatable locatable) {
		Code code = locatable.getLocation().code;
		List<Locatable> list = searchLocatables.get(code);
		if(list == null) return false;
		return list.contains(locatable);
	}


	private int[] getRange(int from, int to) {
		int[] range = new int[to-from];
		for(int i=from; i<to; i++) {
			range[i-from] = i;
		}
		return range;
	}
	
	/**
	 * Generate checkpointing code.
	 */
	@SuppressWarnings("unchecked")
	public void generateCode() {
		/*
		StringTemplateGroup.registerGroupLoader(new CommonGroupLoader("ee/olegus/cpr", null));
		StringTemplateGroup group = StringTemplateGroup.loadGroup("cpr-f9x");
		
		// modules that have global variables to save/restore
		List<String> activeModuleNames = new ArrayList<String>();

		// for every module or program
		for(ProgramUnit unit: parser.getUnits().values()) {
			// generate code for derived types
			generateDerivedTypeCode(group, unit);
		
			// generate save/restore code for module variables
			List vars = findVariableLists(unit, Collections.EMPTY_LIST);
			if(unit.getUnitType()==ProgramUnit.UnitType.MODULE && !vars.isEmpty()) {
				activeModuleNames.add(unit.getName());
				
				CPRFortranTokenStream stream = parser.getFileTokenStreams().get(unit.getFilename());
				Location codeStop = unit.getLocation(LocationType.CODE_STOP);
				StringTemplate module_subprograms_t = group.getInstanceOf("module_subprograms");
				module_subprograms_t.setAttribute("moduleName", unit.getName());
				setVariableLists(module_subprograms_t, vars);
				stream.insertBeforeLine(codeStop.start, module_subprograms_t.toString());
			}
		}
		
		// add template for saving/restoring global variables
		StringTemplate gcprmodule = group.getInstanceOf("gcprmodule");
		gcprmodule.setAttribute("moduleNames", activeModuleNames);
		stringTemplates.put("gcpr.f90", gcprmodule);

		// for all codes that need insertions
		for(Code code: locatables.keySet()) {
			generateCheckpointAdviceCode(group, code);
		}
		
		//
		for(SubroutineCall call: mpiCalls) {
			//Location location = call.getName().getLocation();
			//CPRFortranTokenStream stream = parser.getFileTokenStreams().get(location.code.getFilename());			
			// TODO solve this
			//stream.replace(location.start, "cpr_"+call.getName().getString());
		}*/
	}

	/**
	 * Generate advice (surround existing) code for all needed locations in given code.
	 * 
	 * @param group
	 * @param code
	 */
	@SuppressWarnings("unchecked")
	private void generateCheckpointAdviceCode(StringTemplateGroup group, Code code) {
		/*
		// get places that must be altered
		List<Locatable> codeLocatables = locatables.get(code);
		
		// for all places where we want to insert cpr code
		for(Locatable locatable: codeLocatables) {
			System.out.println("Generating checkpoint code for "+locatable);

			CPRFortranTokenStream stream = parser.getFileTokenStreams().get(locatable.getLocation().code.getFilename());
			List<? extends TypeShape> args;
			if(code instanceof Subprogram) 
				args = ((Subprogram)code).getArguments();
			else
				args = Collections.EMPTY_LIST;

			Location usePart = code.getUpperLocation(Code.LocationType.USE_PART);
			Location declPart = code.getUpperLocation(Code.LocationType.DECL_PART);
			Location execPart = code.getUpperLocation(Code.LocationType.EXEC_PART);

			List<Locatable> processedListForCode = processedLocatables.get(code);
			List<Variable> saveVarList = findVariableLists(code, args);

			// if this code has not been processed yet, insert some code only once
			if(processedListForCode == null) {
				processedListForCode = new ArrayList<Locatable>();
				processedLocatables.put(code, processedListForCode);

				// insert use cpr
				StringTemplate usecpr_t = group.getInstanceOf("usecpr");
				usecpr_t.setAttribute("isMain", code instanceof ProgramUnit);
				stream.insertLine(usePart.stop, usecpr_t.toString());

				// insert needed declarations
				StringTemplate declarations_t = group.getInstanceOf("declarations");
				// TODO solve this
				// stream.insertAfter(declPart.stop, declarations_t.toString());
				
				// insert code that restores
				StringTemplate dorestore_t = group.getInstanceOf("dorestore");
				int[] labels = new int[codeLocatables.size()];
				for(int i=0; i< labels.length; i++)
					labels[i] = i+1;
				dorestore_t.setAttribute("labels", labels);
				dorestore_t.setAttribute("isMain", code instanceof ProgramUnit);
				setVariableLists(dorestore_t, saveVarList);
				stream.insertBeforeLine(execPart.start, dorestore_t.toString());
			}

			int label = processedListForCode.size()+1; // fortran label to jump to
			
			// insert code that check potential checkpoint for emition
			if(locatable instanceof PotentialCheckpoint) {
				StringTemplate pcheckpoint_t = group.getInstanceOf("pcheckpoint");
				pcheckpoint_t.setAttribute("label", label);

				stream.insertAfterLine(locatable.getLocation().stop, pcheckpoint_t.toString());
			}
			
			// insert checkpoint code for this particular locatable
			StringTemplate docheckpoint_t = group.getInstanceOf("docheckpoint");
			docheckpoint_t.setAttribute("label", label);
			docheckpoint_t.setAttribute("isMain", code instanceof ProgramUnit);
			setVariableLists(docheckpoint_t, saveVarList);
			stream.insertAfterLine(locatable.getLocation().stop, docheckpoint_t.toString());
			
			// insert label before procedure/function call
			if(locatable instanceof Call) {
				stream.insertBeforeLine(locatable.getLocation().start, ""+label);
			}

			processedListForCode.add(locatable);
		}*/
	}

	/**
	 * Generate code for saving/restoring derived types declared in given unit.
	 * 
	 * @param group
	 * @param unit
	 */
	private void generateDerivedTypeCode(StringTemplateGroup group, ProgramUnit unit) {
		/*
		// find derived types: type->max dimensions
		Map<Type,Integer> derivedTypes = new HashMap<Type,Integer>(3);
		for(Declaration decl: unit.getDeclarations()) {
			if(decl instanceof Type && !((Type)decl).isIntrinsic()) {
				int maxDimensions = 1; // TODO assume only 1-dimensional arrays for derived types
				derivedTypes.put((Type) decl, maxDimensions);
			}
		}

		// generate save/restore code for derived types
		for(Type type: derivedTypes.keySet()) {
			System.out.println("Generating code for "+type);
			CPRFortranTokenStream stream = parser.getFileTokenStreams().get(type.getLocation().code.getFilename());
			Location codeStop = type.getLocation().code.getLocation(LocationType.CODE_STOP);
			
			StringTemplate derivedType_t = group.getInstanceOf("type_subprograms");
			derivedType_t.setAttribute("type", type);
			List<Variable> varList = new ArrayList<Variable>(type.getDeclarations().size());
			for(Declaration decl: type.getDeclarations()) {
				Variable variable = (Variable) decl;
				varList.add(variable);
			}
			setVariableLists(derivedType_t, varList);
			stream.insertBeforeLine(codeStop.start, derivedType_t.toString());

			int ndimenstions = derivedTypes.get(type);
			
			// generate code for arrays of derived types
			for(int i=1; i<=ndimenstions; i++) {
				StringTemplate derivedTypeDN_t = group.getInstanceOf("type_subprogramsDN");
				derivedTypeDN_t.setAttribute("type", type);
				// create shape array
				derivedTypeDN_t.setAttribute("dimensions", new int[i]);
				stream.insertBeforeLine(codeStop.start, derivedTypeDN_t.toString());
			}
			
			// interfaces for subroutines
			Location declPart = type.getLocation().code.getLocation(LocationType.DECL_PART);
			StringTemplate derivedTypeInterfaces_t = group.getInstanceOf("type_interfaces");
			derivedTypeInterfaces_t.setAttribute("type", type);
			derivedTypeInterfaces_t.setAttribute("numsDimensions", getRange(1, ndimenstions+1));
			stream.insertAfterLine(declPart.stop, derivedTypeInterfaces_t.toString());
		}*/
	}

	
	private List<Variable> findVariableLists(Code code, List<? extends TypeShape> args) {
		List<Variable> varList = new ArrayList<Variable>(5);
		// TODO it is not good to assume order in keySet()
		for(String name: code.getVariables().keySet()) {
			Variable var = code.getVariables().get(name);
			if(args.contains(var)) continue; // TODO but save OUT arguments
			if(var.hasAttribute(Attribute.Type.PARAMETER)) continue;
			if(var.hasAttribute(Attribute.Type.EXTERNAL)) continue;
			varList.add(var);
		}
		
		return varList;
	}
	/**
	 * @param template
	 * @param code
	 * @param args
	 */
	private void setVariableLists(StringTemplate template, List<Variable> varList) {
		for(int i=0; i<varList.size(); i++) {
			Variable var = varList.get(i);
			template.setAttribute("vars.{name,type,pointer,allocatable}", var.getName(), var.getType().getName(), 
					var.hasAttribute(Attribute.Type.POINTER),var.hasAttribute(Attribute.Type.ALLOCATABLE));
		}
		for(int i=varList.size()-1; i>=0; i--) {
			Variable var = varList.get(i);
			template.setAttribute("reverseVars.{name,type,pointer,allocatable}", var.getName(), var.getType().getName(),
					var.hasAttribute(Attribute.Type.POINTER), var.hasAttribute(Attribute.Type.ALLOCATABLE));
		}
	}
	
	public void createReferenceTable() {
		/*
		for(ProgramUnit unit: parser.getUnits().values()) {
			createReferenceTable(unit);
		}
		
		for(References references: this.references.values()) {
			System.out.println(references);
		}*/
	}

	/**
	 * @param code
	 */
	private void createReferenceTable(Code code) {
		for(Subprogram subprogram: code.getSubprograms().values()) {
			createReferenceTable(subprogram);
		}
		
		for(Statement statement: code.getConstructs()) {
			if(statement instanceof Call) {
				// add reference to table
				Call call = (Call) statement;
				Callable callable = call.getCallable();
				if(!this.references.containsKey(callable))
					this.references.put(callable, new References(callable));
				References references = this.references.get(callable);
				references.getCalls().add(call);
			}
			
			// parse executable statements for function calls
			// TODO structure the code
			if(statement instanceof Executable) {
				Executable executable = (Executable) statement;
				for(Iterator<Expression> iter = executable.getExpressions(); iter.hasNext(); ) {
					Expression expression = iter.next();
					if(expression instanceof Reference) { // unresolved reference
						Expression resolvedReference = ((Reference)expression).getResolvedReference();
						if(resolvedReference instanceof FunctionCall) {
							Call call = (Call) resolvedReference;
							Callable callable = call.getCallable();
							if(!this.references.containsKey(callable))
								this.references.put(callable, new References(callable));
							References references = this.references.get(callable);
							references.getCalls().add(call);
						}
					}
				}
			}
		}
	}	
}

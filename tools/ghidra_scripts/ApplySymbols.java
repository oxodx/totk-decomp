import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;

// Apply the project's raw-address names before exporting pseudocode.
// @category TOTK

public class ApplySymbols extends GhidraScript {

  private void apply(File csv, boolean functionManifest) throws Exception {
    long imageBase = currentProgram.getImageBase().getOffset();
    try (BufferedReader reader = new BufferedReader(new FileReader(csv))) {
      String line;
      boolean header = true;
      while ((line = reader.readLine()) != null) {
        line = line.trim();
        if (line.isEmpty() || line.startsWith("#")) continue;
        if (header) {
          header = false;
          continue;
        }
        String[] fields = line.split(",", -1);
        if (fields.length < 3) continue;
        long rawAddress = Long.decode(fields[0].trim());
        String name = (functionManifest ? fields[2] : fields[1]).trim();
        String kind = functionManifest ? "function" : fields[2].trim();
        if (name.isEmpty()) continue;
        Address address = currentProgram
          .getAddressFactory()
          .getDefaultAddressSpace()
          .getAddress(imageBase + rawAddress);
        Function function = currentProgram
          .getFunctionManager()
          .getFunctionAt(address);
        if (kind.equals("function") && function != null) {
          function.setName(name, SourceType.USER_DEFINED);
        } else {
          currentProgram
            .getSymbolTable()
            .createLabel(address, name, SourceType.USER_DEFINED);
        }
      }
    }
  }

  @Override
  public void run() throws Exception {
    String[] args = getScriptArgs();
    if (args.length != 2) throw new IllegalArgumentException(
      "Expected functions.csv and symbols.csv"
    );
    apply(new File(args[0]), true);
    apply(new File(args[1]), false);
    println("Applied project function and symbol names");
  }
}

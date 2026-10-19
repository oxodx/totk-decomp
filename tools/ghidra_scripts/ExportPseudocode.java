import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressRangeIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

// Export paired C-like pseudocode and exact assembly for every function.
// @category TOTK

public class ExportPseudocode extends GhidraScript {

  private static String safeName(String value) {
    return value.replaceAll("[^A-Za-z0-9_]", "_");
  }

  private static String hexBytes(byte[] bytes) {
    StringBuilder text = new StringBuilder();
    for (byte value : bytes) {
      text.append(String.format("%02x", value & 0xff));
    }
    return text.toString();
  }

  private static String operands(Instruction instruction) {
    StringBuilder text = new StringBuilder();
    for (int i = 0; i < instruction.getNumOperands(); i++) {
      if (i != 0) {
        text.append(", ");
      }
      text.append(instruction.getDefaultOperandRepresentation(i));
    }
    return text.toString();
  }

  private void exportAssembly(Function function, File file) throws Exception {
    Listing listing = currentProgram.getListing();
    StringBuilder output = new StringBuilder();
    output.append(
      "// GHIDRA DISASSEMBLY — verify undecoded words with another AArch64 disassembler\n"
    );
    output.append(
      String.format(
        "// %s @ 0x%x\n\n",
        function.getName(),
        function.getEntryPoint().getOffset()
      )
    );
    AddressRangeIterator ranges = function.getBody().getAddressRanges(true);
    while (ranges.hasNext()) {
      AddressRange range = ranges.next();
      Address cursor = range.getMinAddress();
      while (cursor.compareTo(range.getMaxAddress()) <= 0) {
        Instruction instruction = listing.getInstructionAt(cursor);
        if (instruction != null) {
          byte[] bytes = instruction.getBytes();
          output.append(
            String.format(
              "%016x  %-16s  %-10s %s\n",
              cursor.getOffset(),
              hexBytes(bytes),
              instruction.getMnemonicString(),
              operands(instruction)
            )
          );
          cursor = cursor.add(instruction.getLength());
        } else {
          byte[] bytes = new byte[4];
          int count = currentProgram.getMemory().getBytes(cursor, bytes);
          if (count <= 0) {
            break;
          }
          long word = 0;
          for (int i = 0; i < count; i++) {
            word |= (long) (bytes[i] & 0xff) << (8 * i);
          }
          output.append(
            String.format(
              "%016x  %-16s  .word      0x%08x  // undecoded\n",
              cursor.getOffset(),
              hexBytes(bytes),
              word
            )
          );
          cursor = cursor.add(Math.min(4, count));
        }
      }
    }
    Files.writeString(file.toPath(), output.toString(), StandardCharsets.UTF_8);
  }

  @Override
  public void run() throws Exception {
    String[] args = getScriptArgs();
    if (args.length != 1) {
      throw new IllegalArgumentException("Expected output directory argument");
    }
    File output = new File(args[0]);
    File cDirectory = new File(output, "c");
    File asmDirectory = new File(output, "asm");
    cDirectory.mkdirs();
    asmDirectory.mkdirs();
    File indexFile = new File(output, "functions.csv");
    DecompInterface decompiler = new DecompInterface();
    decompiler.toggleCCode(true);
    decompiler.toggleSyntaxTree(true);
    if (!decompiler.openProgram(currentProgram)) {
      throw new RuntimeException(
        "Ghidra decompiler could not open the program"
      );
    }
    try (BufferedWriter index = new BufferedWriter(new FileWriter(indexFile))) {
      index.write("address,size,name,c,asm,c_status\n");
      FunctionIterator functions = currentProgram
        .getFunctionManager()
        .getFunctions(true);
      while (functions.hasNext() && !monitor.isCancelled()) {
        Function function = functions.next();
        long address = function.getEntryPoint().getOffset();
        long size = function.getBody().getNumAddresses();
        String stem = String.format(
          "%08x_%s",
          address,
          safeName(function.getName())
        );
        String asmPath = "asm/" + stem + ".s";
        exportAssembly(function, new File(output, asmPath));

        String cPath = "";
        String cStatus = "failed";
        DecompileResults result = decompiler.decompileFunction(
          function,
          60,
          monitor
        );
        if (
          result.decompileCompleted() && result.getDecompiledFunction() != null
        ) {
          cPath = "c/" + stem + ".c";
          String banner =
            "/* GHIDRA PSEUDOCODE — UNVERIFIED, MAY BE WRONG, DOES NOT COUNT AS SOURCE */\n\n";
          Files.writeString(
            new File(output, cPath).toPath(),
            banner + result.getDecompiledFunction().getC(),
            StandardCharsets.UTF_8
          );
          cStatus = "ok";
        }
        index.write(
          String.format(
            "0x%x,0x%x,%s,%s,%s,%s\n",
            address,
            size,
            safeName(function.getName()),
            cPath,
            asmPath,
            cStatus
          )
        );
      }
    } finally {
      decompiler.dispose();
    }
    println(
      "C-like pseudocode and assembly exported to " + output.getAbsolutePath()
    );
  }
}

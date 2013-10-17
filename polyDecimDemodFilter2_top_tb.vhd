

  -- clock process for generating 100 MHz clock
  clk_process :process
  begin
    clk1 <= '0';
    wait for clk1_period/2;
    clk1 <= '1';
    wait for clk1_period/2;
  
end process;
-- -----------------------------------------------------------------------------------	
-- 	File Writer Block										
-- -----------------------------------------------------------------------------------

-- ----------------------------------------------------------
-- 	digitalDemodTest_top
-- ----------------------------------------------------------
output_file_tValidOut_NCO : entity work.file_writer 							  	
	   generic map(																			  	
	     dataWidth => 1,													  	
	     wordWidth => 1,																																				
	     fileName => "/home/nick/polyDecimDemodFilter2/datatValidOut_NCOoutput.dat"			
	   )																							
	   port map( 																					
	     reset => rst,																			
	     clk => clk,																				
	     enable => rst,																			
	     data => tValidOut_NCO,														
	     data_valid => rst																		
	   );
output_file_tValidOut : entity work.file_writer 							  	
	   generic map(																			  	
	     dataWidth => 1,													  	
	     wordWidth => 1,																																				
	     fileName => "/home/nick/polyDecimDemodFilter2/datatValidOutoutput.dat"			
	   )																							
	   port map( 																					
	     reset => rst,																			
	     clk => clk,																				
	     enable => rst,																			
	     data => tValidOut,														
	     data_valid => rst																		
	   );
output_file_outputDemodRe : entity work.file_writer 							  	
	   generic map(																			  	
	     dataWidth => 35,													  	
	     wordWidth => 1,																																				
	     fileName => "/home/nick/polyDecimDemodFilter2/dataoutputDemodReoutput.dat"			
	   )																							
	   port map( 																					
	     reset => rst,																			
	     clk => clk,																				
	     enable => rst,																			
	     data => outputDemodRe,														
	     data_valid => rst																		
	   );
output_file_outputDemodIm : entity work.file_writer 							  	
	   generic map(																			  	
	     dataWidth => 35,													  	
	     wordWidth => 1,																																				
	     fileName => "/home/nick/polyDecimDemodFilter2/dataoutputDemodImoutput.dat"			
	   )																							
	   port map( 																					
	     reset => rst,																			
	     clk => clk,																				
	     enable => rst,																			
	     data => outputDemodIm,														
	     data_valid => rst																		
	   );

-- ----------------------------------------------------------------------------------- 	
-- 	End of File Writer Block										
-- -----------------------------------------------------------------------------------
										
-- -----------------------------------------------------------------------------------
										

  --------------------------------------------------------------------------
  -- Begin Simulation Process 
  --------------------------------------------------------------------------
  sim_process : process is

  --<<<<<<<<<<<<<<<<<<< OKHOSTCALLS START PASTE HERE >>>>>>>>>>>>>>>>>>>>-- 
  
-- User defined data for pipe procedures
    -----------------------------------------------------------------------
    variable BlockDelayStates : integer := 5;  -- REQUIRED: # of clocks between blocks of pipe data
    variable ReadyCheckDelay  : integer := 5;  -- REQUIRED: # of clocks before block transfer before
                                               --    host interface checks for ready (0-255)
    variable PostReadyDelay   : integer := 5;  -- REQUIRED: # of clocks after ready is asserted and
                                               --    check that the block transfer begins (0-255)
    variable pipeInSize       : integer := 1024; 
    variable pipeOutSize      : integer := 1024;
  
    -- If you require multiple pipe arrays, you may create more arrays here
    -- duplicate the desired pipe procedures as required, change the names
    -- of the duplicated procedure to a unique identifiers, and alter the
    -- pipe array in that procedure to your newly generated arrays here.
    type PIPEIN_ARRAY is array (0 to pipeInSize - 1) of std_logic_vector(7 downto 0);
    variable pipeIn   : PIPEIN_ARRAY;
  
    type PIPEOUT_ARRAY is array (0 to pipeOutSize - 1) of std_logic_vector(7 downto 0);
    variable pipeOut  : PIPEOUT_ARRAY;
  
    -----------------------------------------------------------------------
    -- Required data for procedures and functions
    -----------------------------------------------------------------------
    type STD_ARRAY is array (0 to 31) of std_logic_vector(15 downto 0);
    variable WireIns, WireOuts, Triggered  :  STD_ARRAY;
  
    constant DNOP                   : std_logic_vector(3 downto 0) := x"0";
    constant DReset                 : std_logic_vector(3 downto 0) := x"1";
    constant DUpdateWireIns         : std_logic_vector(3 downto 0) := x"3";
    constant DUpdateWireOuts        : std_logic_vector(3 downto 0) := x"5";
    constant DActivateTriggerIn     : std_logic_vector(3 downto 0) := x"6";
    constant DUpdateTriggerOuts     : std_logic_vector(3 downto 0) := x"7";
    constant DWriteToPipeIn         : std_logic_vector(3 downto 0) := x"9";
    constant DReadFromPipeOut       : std_logic_vector(3 downto 0) := x"a";
    constant DWriteToBlockPipeIn    : std_logic_vector(3 downto 0) := x"b";
    constant DReadFromBlockPipeOut  : std_logic_vector(3 downto 0) := x"c";
  
    -----------------------------------------------------------------------
    -- FrontPanelReset
    -----------------------------------------------------------------------
    procedure FrontPanelReset is
      variable i : integer := 0;
    begin
        for i in 31 downto 0 loop
          WireIns(i) := (others => '0');
          WireOuts(i) := (others => '0');
          Triggered(i) := (others => '0');
        end loop;
  
        wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DReset;
        wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
        wait until (hi_out(0) = '0');
    end procedure FrontPanelReset;
  
    -----------------------------------------------------------------------
    -- SetWireInValue
    -----------------------------------------------------------------------
    procedure SetWireInValue (
      ep   : in  std_logic_vector(7 downto 0);
      val  : in  std_logic_vector(15 downto 0);
      mask : in  std_logic_vector(15 downto 0)) is
      
      variable tmp_slv16 :     std_logic_vector(15 downto 0);
      variable tmpI      :     integer;
    begin
      tmpI := CONV_INTEGER(ep);
      tmp_slv16 := WireIns(tmpI) and (not mask);
      WireIns(tmpI) := (tmp_slv16 or (val and mask));
    end procedure SetWireInValue;
  
    -----------------------------------------------------------------------
    -- GetWireOutValue
    -----------------------------------------------------------------------
    impure function GetWireOutValue (
      ep : std_logic_vector) return std_logic_vector is
      
      variable tmp_slv16 : std_logic_vector(15 downto 0);
      variable tmpI      : integer;
    begin
      tmpI := CONV_INTEGER(ep);
      tmp_slv16 := WireOuts(tmpI - 16#20#);
      return (tmp_slv16);
    end GetWireOutValue;
  
    -----------------------------------------------------------------------
    -- IsTriggered
    -----------------------------------------------------------------------
    impure function IsTriggered (
      ep   : std_logic_vector;
      mask : std_logic_vector(15 downto 0)) return BOOLEAN is
      
      variable tmp_slv16   : std_logic_vector(15 downto 0);
      variable tmpI        : integer;
      variable msg_line    : line;
    begin
      tmpI := CONV_INTEGER(ep);
      tmp_slv16 := (Triggered(tmpI - 16#60#) and mask);
  
      if (tmp_slv16 >= 0) then
        if (tmp_slv16 = 0) then
          return FALSE;
        else
          return TRUE;
        end if;
      else
        write(msg_line, STRING'("***FRONTPANEL ERROR: IsTriggered mask 0x"));
        hwrite(msg_line, mask);
        write(msg_line, STRING'(" covers unused Triggers"));
        writeline(output, msg_line);
        return FALSE;        
      end if;     
    end IsTriggered;
  
    -----------------------------------------------------------------------
    -- UpdateWireIns
    -----------------------------------------------------------------------
    procedure UpdateWireIns is
      variable i : integer := 0;
    begin
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DUpdateWireIns; wait for 1 ps;
      hi_in(1) <= '1'; wait for 1 ps;
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP; wait for 1 ps;
      for i in 0 to 31 loop
        hi_dataout <= WireIns(i); wait for 1 ps; wait until (rising_edge(hi_clk)); wait for 1 ps;
      end loop;
      wait until (hi_out(0) = '0'); wait for 1 ps; 
    end procedure UpdateWireIns;
     
    -----------------------------------------------------------------------
    -- UpdateWireOuts
    -----------------------------------------------------------------------
    procedure UpdateWireOuts is
      variable i : integer := 0;
    begin
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DUpdateWireOuts; wait for 1 ps;
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP; wait for 1 ps;
      wait until (rising_edge(hi_clk)); hi_in(1) <= '0'; wait for 1 ps;
      wait until (rising_edge(hi_clk)); wait until (rising_edge(hi_clk)); wait for 1 ps;
      for i in 0 to 31 loop
        wait until (rising_edge(hi_clk)); WireOuts(i) := hi_inout; wait for 1 ps;
      end loop;
      wait until (hi_out(0) = '0'); wait for 1 ps;
    end procedure UpdateWireOuts;
  
    -----------------------------------------------------------------------
    -- ActivateTriggerIn
    -----------------------------------------------------------------------
    procedure ActivateTriggerIn (
      ep  : in  std_logic_vector(7 downto 0);
      bit : in  integer) is 
      
      variable tmp_slv4 :     std_logic_vector(3 downto 0);
    begin
      tmp_slv4 := CONV_std_logic_vector(bit, 4);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DActivateTriggerIn;
      hi_in(1) <= '1';
      hi_dataout <= (x"00" & ep);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      hi_dataout <= SHL(x"0001", tmp_slv4);
      wait until (rising_edge(hi_clk)); hi_dataout <= x"0000";
      wait until (hi_out(0) = '0');
    end procedure ActivateTriggerIn;
  
    -----------------------------------------------------------------------
    -- UpdateTriggerOuts
    -----------------------------------------------------------------------
    procedure UpdateTriggerOuts is
      variable i: integer := 0;
    begin
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DUpdateTriggerOuts;
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      wait until (rising_edge(hi_clk)); hi_in(1) <= '0';
      wait until (rising_edge(hi_clk)); wait until (rising_edge(hi_clk));
      wait until (rising_edge(hi_clk));
      
      for i in 0 to (UPDATE_TO_READOUT_CLOCKS-1) loop
          wait until (rising_edge(hi_clk));  
      end loop;
      
      for i in 0 to 31 loop
        wait until (rising_edge(hi_clk)); Triggered(i) := hi_inout;
      end loop;
      wait until (hi_out(0) = '0');
    end procedure UpdateTriggerOuts;
  
    -----------------------------------------------------------------------
    -- WriteToPipeIn
    -----------------------------------------------------------------------
    procedure WriteToPipeIn (
      ep      : in  std_logic_vector(7 downto 0);
      length  : in  integer) is
  
      variable len, i, j, k, blockSize : integer;
      variable tmp_slv8                : std_logic_vector(7 downto 0);
      variable tmp_slv32               : std_logic_vector(31 downto 0);
    begin
      len := (length / 2); j := 0; k := 0; blockSize := 1024;
      tmp_slv8 := CONV_std_logic_vector(BlockDelayStates, 8);
      tmp_slv32 := CONV_std_logic_vector(len, 32);
      wait until (rising_edge(hi_clk)); hi_in(1) <= '1';
      hi_in(7 downto 4) <= DWriteToPipeIn;
      hi_dataout <= (tmp_slv8 & ep);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      hi_dataout <= tmp_slv32(15 downto 0);
      wait until (rising_edge(hi_clk));
      hi_dataout <= tmp_slv32(31 downto 16);
      for i in 0 to len - 1 loop
        wait until (rising_edge(hi_clk));
        hi_dataout(7 downto 0) <= pipeIn(i*2);
        hi_dataout(15 downto 8) <= pipeIn((i*2)+1);
        j := j + 2;
        if (j = blockSize) then
          for k in 0 to BlockDelayStates - 1 loop
            wait until (rising_edge(hi_clk));
          end loop;
          j := 0;
        end if;
      end loop;
      wait until (hi_out(0) = '0');
    end procedure WriteToPipeIn;
  
    -----------------------------------------------------------------------
    -- ReadFromPipeOut
    -----------------------------------------------------------------------
    procedure ReadFromPipeOut (
      ep     : in  std_logic_vector(7 downto 0);
      length : in  integer) is
      
      variable len, i, j, k, blockSize : integer;
      variable tmp_slv8                : std_logic_vector(7 downto 0);
      variable tmp_slv32               : std_logic_vector(31 downto 0);
    begin
      len := (length / 2); j := 0; blockSize := 1024;
      tmp_slv8 := CONV_std_logic_vector(BlockDelayStates, 8);
      tmp_slv32 := CONV_std_logic_vector(len, 32);
      wait until (rising_edge(hi_clk)); hi_in(1) <= '1';
      hi_in(7 downto 4) <= DReadFromPipeOut;
      hi_dataout <= (tmp_slv8 & ep);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      hi_dataout <= tmp_slv32(15 downto 0);
      wait until (rising_edge(hi_clk));
      hi_dataout <= tmp_slv32(31 downto 16);
      wait until (rising_edge(hi_clk));
      hi_in(1) <= '0';
      for i in 0 to len - 1 loop
        wait until (rising_edge(hi_clk));
        pipeOut(i*2) := hi_inout(7 downto 0);
        pipeOut((i*2)+1) := hi_inout(15 downto 8);
        j := j + 2;
        if (j = blockSize) then
          for k in 0 to BlockDelayStates - 1 loop
            wait until (rising_edge(hi_clk));
          end loop;
          j := 0;
        end if;
      end loop;
      wait until (hi_out(0) = '0');
    end procedure ReadFromPipeOut;
  
    -----------------------------------------------------------------------
    -- WriteToBlockPipeIn
    -----------------------------------------------------------------------
    procedure WriteToBlockPipeIn (
      ep          : in std_logic_vector(7 downto 0);
      blockLength : in integer;
      length      : in integer) is
      
      variable len, i, j, k, blockSize, blockNum : integer;
      variable tmp_slv8                          : std_logic_vector(7 downto 0);
      variable tmp_slv16                         : std_logic_vector(15 downto 0);
      variable tmp_slv32                         : std_logic_vector(31 downto 0);
    begin
  
      len := (length/2); blockSize := (blockLength/2); j := 0; k := 0;
      blockNum := (len/blockSize);
      tmp_slv8 := CONV_std_logic_vector(BlockDelayStates, 8);
      tmp_slv32 := CONV_std_logic_vector(len, 32);
      wait until (rising_edge(hi_clk)); hi_in(1) <= '1';
      hi_in(7 downto 4) <= DWriteToBlockPipeIn;
      hi_dataout <= (tmp_slv8 & ep);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      hi_dataout <= tmp_slv32(15 downto 0);
      wait until (rising_edge(hi_clk)); hi_dataout <= tmp_slv32(31 downto 16);
      tmp_slv16 := CONV_std_logic_vector(blockSize, 16);
      wait until (rising_edge(hi_clk)); hi_dataout <= tmp_slv16;
      wait until (rising_edge(hi_clk));
      tmp_slv16 := (CONV_std_logic_vector(PostReadyDelay, 8) & CONV_std_logic_vector(ReadyCheckDelay, 8));
      hi_dataout <= tmp_slv16;
      for i in 1 to blockNum loop
        while (hi_out(0) = '1') loop wait until (rising_edge(hi_clk)); end loop;
        while (hi_out(0) = '0') loop wait until (rising_edge(hi_clk)); end loop;
        wait until (rising_edge(hi_clk)); wait until (rising_edge(hi_clk));
        for j in 1 to blockSize loop
          hi_dataout(7 downto 0) <= pipeIn(k);
          hi_dataout(15 downto 8) <= pipeIn(k+1);
          wait until (rising_edge(hi_clk)); k:=k+2;
        end loop;
        for j in 1 to BlockDelayStates loop 
          wait until (rising_edge(hi_clk)); 
        end loop;
      end loop;
      wait until (hi_out(0) = '0');
    end procedure WriteToBlockPipeIn;
  
    -----------------------------------------------------------------------
    -- ReadFromBlockPipeOut
    -----------------------------------------------------------------------
    procedure ReadFromBlockPipeOut (
      ep          : in std_logic_vector(7 downto 0);
      blockLength : in integer;
      length      : in integer) is
      
      variable len, i, j, k, blockSize, blockNum : integer;
      variable tmp_slv8                          : std_logic_vector(7 downto 0);
      variable tmp_slv16                         : std_logic_vector(15 downto 0);
      variable tmp_slv32                         : std_logic_vector(31 downto 0);
    begin
      len := (length/2); blockSize := (blockLength/2); j := 0; k := 0;
      blockNum := (len/blockSize);
      tmp_slv8 := CONV_std_logic_vector(BlockDelayStates, 8);
      tmp_slv32 := CONV_std_logic_vector(len, 32);
      wait until (rising_edge(hi_clk));
      hi_in(1) <= '1';
      hi_in(7 downto 4) <= DReadFromBlockPipeOut;
      hi_dataout <= (tmp_slv8 & ep);
      wait until (rising_edge(hi_clk)); hi_in(7 downto 4) <= DNOP;
      hi_dataout <= tmp_slv32(15 downto 0);
      wait until (rising_edge(hi_clk)); hi_dataout <= tmp_slv32(31 downto 16);
      tmp_slv16 := CONV_std_logic_vector(blockSize, 16);
      wait until (rising_edge(hi_clk)); hi_dataout <= tmp_slv16;
      wait until (rising_edge(hi_clk));
      tmp_slv16 := (CONV_std_logic_vector(PostReadyDelay, 8) & CONV_std_logic_vector(ReadyCheckDelay, 8));
      hi_dataout <= tmp_slv16;
      wait until (rising_edge(hi_clk)); hi_in(1) <= '0';
      for i in 1 to blockNum loop
        while (hi_out(0) = '1') loop wait until (rising_edge(hi_clk)); end loop;
        while (hi_out(0) = '0') loop wait until (rising_edge(hi_clk)); end loop;
        wait until (rising_edge(hi_clk)); wait until (rising_edge(hi_clk));
        for j in 1 to blockSize loop
          pipeOut(k) := hi_inout(7 downto 0); pipeOut(k+1) := hi_inout(15 downto 8);
          wait until (rising_edge(hi_clk)); k:=k+2;
        end loop;
        for j in 1 to BlockDelayStates loop wait until (rising_edge(hi_clk)); end loop;
      end loop;
      wait until (hi_out(0) = '0');
    end procedure ReadFromBlockPipeOut;




-- wireInLines unpacked:
-- [    | reloadCoef | runFIRFilter | run_mac | load_ram | rst ]
-- [    |    4       |    3         |      2  |   1      |  0  ]

   -- Stimulus process
   
   begin		


    FrontPanelReset;

      
      -- hold reset state for 100 ns.
      wait for 100 ns;	

      wait for clk1_period*10;
      report "Starting Simulation...";

      decimFactor <= 4;

      report "Pump the reset line...";
      -- set rst high:
      wireInLines <= x"0001"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;


      wireInLines <= x"0000"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;

      wait for clk1_period*10;

      -- load_ram high:
      wireInLines <= x"0002"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;
      report "Writing coefficients to block ram...";
      for i in 0 to windowSize loop
        windowCoef <= myCoef(i); wait until (rising_edge(clk1)); 
        SetWireInValue(x"03",std_logic_vector(conv_unsigned(i,16)),x"ffff");
        SetWireInValue(x"02",inputSignal,x"ffff");
        SetWireInValue(x"05",windowCoef(31 downto 16),x"ffff");
        SetWireInValue(x"06",windowCoef(15 downto 0),x"ffff");
        UpdateWireIns;
        ActivateTriggerIn(x"40",0);
        report "Address: " & integer'image(i);
      end loop;

      report "Writing inputSignal to wireIn...";
      for i in 0 to inputSize loop
        inputSignal <= myCosine(i); wait until (rising_edge(clk1)); 
        SetWireInValue(x"03",std_logic_vector(conv_unsigned(i,16)),x"ffff");
        SetWireInValue(x"02",inputSignal,x"ffff");
        SetWireInValue(x"05",windowCoef(31 downto 16),x"ffff");
        SetWireInValue(x"06",windowCoef(15 downto 0),x"ffff");
        UpdateWireIns;
        ActivateTriggerIn(x"40",0);
        report "Address: " & integer'image(i);
      end loop;

  
      wireInLines <= x"0000"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;

      -- runFilter high:
      wireInLines <= x"000C"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;
      report "Set Phase Increment for NCO...";
      phaseInc <= x"147A"; wait until (rising_edge(clk1));
      SetWireInValue(x"01",phaseInc,x"ffff");
      UpdateWireIns;      

      wait for 13 us;

      report "Read data back from wireouts...";
      for i in 0 to windowSize loop
        -- SetWireInValue(x"04",std_logic_vector(conv_unsigned(i,16)),x"ffff"); 
        report "Address: " & integer'image(i);
        acc_padRe2(63 downto 48) <= GetWireOutValue(x"20"); -- wait until (rising_edge(ti_clk)); 
        acc_padRe2(47 downto 32) <= GetWireOutValue(x"21"); -- wait until (rising_edge(ti_clk)); 
        acc_padRe2(31 downto 16) <= GetWireOutValue(x"22"); -- wait until (rising_edge(ti_clk)); 
        acc_padRe2(15 downto 0) <= GetWireOutValue(x"23"); -- wait until (rising_edge(ti_clk)); 

        acc_padIm2(63 downto 48) <= GetWireOutValue(x"24"); -- wait until (rising_edge(ti_clk)); 
        acc_padIm2(47 downto 32) <= GetWireOutValue(x"25"); -- wait until (rising_edge(ti_clk)); 
        acc_padIm2(31 downto 16) <= GetWireOutValue(x"26"); -- wait until (rising_edge(ti_clk)); 
        acc_padIm2(15 downto 0) <= GetWireOutValue(x"27"); -- wait until (rising_edge(ti_clk)); 
        UpdateWireOuts;
      end loop;

      wireInLines <= x"0000"; wait until (rising_edge(clk1));
      SetWireInValue(x"00",wireInLines,x"ffff");
      UpdateWireIns;
      

      report "Finished Processing.";


     wait;
   end process;
end behavior;




'''
.. module:: skrf.vi.vna
=================================================================
Vector Network Analyzers (:mod:`skrf.vi.vna`)
=================================================================

.. warning:: 
    
    These Virtual Instruments are very spotily written, and may be subject 
    to major re-writing in the future. 

.. autosummary::
    :toctree: generated/

    PNA
    ZVA40
    HP8510C
    HP8720
'''
import numpy as npy
import visa
from visa import GpibInstrument
from warnings import warn

from ..frequency import *
from ..network import *
from .. import mathFunctions as mf



class PNA(GpibInstrument):
    '''
    Agilent PNA[X] 
    
    Below are lists of some high-level commands sorted by functionality. 


    Object IO
    
    .. hlist:: 
        :columns: 2
        
        * :func:`get_oneport`
        * :func:`get_twoport`
        * :func:`get_frequency`
        * :func:`get_network`
        * :func:`get_network_all_meas`
    
    
    Simple IO
    
    .. hlist:: 
        :columns: 2
        
        * :func:`get_data_snp`
        * :func:`get_data`
        * :func:`get_sdata`
        * :func:`get_fdata`
        * :func:`get_rdata`
    
    
    Examples
    -----------
    
    >>> from skrf.vi.vna import PNA
    >>> v = PNA()
    >>> n = v.get_oneport()
    >>> n = v.get_twoport()
    
    
    Notes
    --------
    This instrument references `measurements` and `traces`. Traces are 
    displayed traces, while measurements are active measurements on the 
    VNA which may or may not be displayed on screen.
    '''
    def __init__(self, address=16, channel=1,timeout = 3, echo = False,
        front_panel_lockout= False, **kwargs):
        '''
        Constructor 
        
        Parameters
        -------------
        address : int
            GPIB address 
        channel : int
            set active channel. Most commands operate on the active channel
        timeout : number
            GPIB command timeout in seconds. 
        echo : Boolean
            echo  all strings passed to the write command to stdout. 
            useful for troubleshooting
        front_panel_lockout : Boolean
            lockout front panel during operation. 
        \*\*kwargs : 
            passed to :func:`visa.GpibInstrument.__init__`
        '''
        GpibInstrument.__init__(self,
            'GPIB::'+str(address),
            timeout=timeout,
            **kwargs)
            
        self.channel=channel
        self.port = 1
        self.echo = echo
        if not front_panel_lockout:
            self.gtl()
            
            
    def write(self, msg, *args, **kwargs):
        '''
        Write a msg to the instrument. 
        '''
        if self.echo:
            print msg 
        return GpibInstrument.write(self,msg, *args, **kwargs)
    
    write.__doc__ = GpibInstrument.write.__doc__
    
    ## BASIC GPIB
    @property
    def idn(self):
        '''
        Identifying string for the instrument
        '''
        return self.ask('*IDN?')
    
    def opc(self):
        '''
        Ask for indication that operations complete
        '''
        return self.ask('*OPC?')
    
    def gtl(self):
        '''
        Go to local. 
        '''
        self._vpp43.gpib_control_ren(
            self.vi, 
            self._vpp43.VI_GPIB_REN_DEASSERT_GTL,
            )
    
    def rst(self):
        '''
        reset 
        '''
        self.write('*RST;')    
            
    ## triggering        
    @property
    def continuous(self):
        '''
        Set continuous sweeping ON/OFF 
        '''
        return (self.ask('sense:sweep:mode?')=='CONT')

    @continuous.setter
    def continuous(self, val):
        '''
        '''
        if val:
            self.write('sense:sweep:mode cont')
        else:
            self.write('sense:sweep:mode hold')
    
    def sweep(self):
        '''
        Initiates a sweep and waits for it to complete before returning
        
        If vna is in continuous sweep mode then this puts it back
        '''
        was_cont = self.continuous
        out = bool(self.ask("SENS:SWE:MODE SINGle;*OPC?"))
        self.continuous = was_cont
        return out
    
    def get_sweep_type(self):
        '''
        Sets the type of analyzer sweep mode. First set sweep type, then set sweep 
        parameters such as frequency or power settings.
        
        Parameters
        -------------
        val: str
            Choose from:
                LINear | LOGarithmic | POWer | CW | SEGMent | PHASe
                Note: SWEep TYPE cannot be set to SEGMent if there 
                are no segments t
        '''
        return self.ask('sense%i:sweep:type?'%self.channel)
    
    def set_sweep_type(self,val):
        self.write('sense%i:sweep:type %s'%(self.channel,val))
        
    sweep_type = property(get_sweep_type, set_sweep_type)
    def get_sweep_mode(self):
        '''
        Sets the number of trigger signals the specified channel will ACCEPT.
        See Triggering the PNA Using SCPI.
        
        Parameters
        -------------
        val: str 
            Trigger mode. Choose from:
            HOLD - channel will not trigger
            CONTinuous - channel triggers indefinitely
            GROups - channel accepts the number of triggers specified with the last
            SENS:SWE:GRO:COUN <num>. This is one of the PNA overlapped
            commands. Learn more.
            SINGle - channel accepts ONE trigger, then goes to HOLD.
        '''
        return self.ask('sense%i:sweep:mode?'%self.channel)
    
    def set_sweep_mode(self,val):
        self.write('sense%i:sweep:mode %s'%(self.channel,val))
    
    sweep_mode = property(get_sweep_mode, set_sweep_mode)
    
    
    def get_trigger_mode(self):
        '''
        Sets and reads the trigger mode for the specified channel. 
        This determines what EACH signal will trigger.
        
        values
        ----------
        
        ['channel','sweep','point','trace']

        '''
        return self.ask('sense%i:sweep:trigger:mode?'%self.channel)
    
    def set_trigger_mode(self,val):
        if val.lower() not in ['channel','sweep','point','trace']:
            raise ValueError('value must be a boolean')
        
        self.write('sense%i:sweep:trigger:mode %s'%(self.channel, val))
    
    trigger_mode = property(get_trigger_mode, set_trigger_mode)
    
    def get_trigger_source(self):
        '''
        Sets the source of the sweep trigger signal. This command is 
        a super-set of INITiate:CONTinuous which can NOT set the 
        source to External.
        
        values
        --------
        
        EXTernal - external (rear panel) source.
        IMMediate - internal source sends continuous trigger signals
        MANual - sends one trigger signal when manually triggered from 
            the front panel or INIT:IMM is sent.
        '''
        return self.ask('trigger:sequence:source?')
    
    def set_trigger_source(self,val):
        '''
        '''
        self.write('trigger:sequence:source %s'%val)
    
    trigger_source = property(get_trigger_source, set_trigger_source)
    
    def trigger(self):
        '''
        sent a manual trigger signal
        '''
        self.write('INIT:IMM')
    
    def trigger_and_wait_till_done(self):
        '''
        send a manual trigger signal, and dont return untill operation
        is completed
        '''
        self.trigger()
        self.opc()
        
    ## power
    def get_power_level(self):
        '''
        Get the RF power level
        '''
        return float(self.ask('SOURce:POWer?'))
    
    def set_power_level(self, num, cnum=None, port=None):
        '''
        Set the RF power level 
        
        Parameters 
        -----------
        num : float
            Source power in dBm
        
        '''
        if cnum is None:
            cnum = self.channel
        
        if port is None:
            port = self.port
        
        self.write('SOURce%i:POWer%i %f'%(cnum, port, num))
    
    power_level = property(get_power_level, set_power_level)
    
    def toggle_port_power(self,on=True, port =1):
        '''
        Turn a given port's power on or off 
        
        Parameters
        ----------
        on : bool
            turn power on or not 
        port : int 
            the port (duh)
        '''
        if on:
            mode = 'on'
        else:
            mode = 'off'
        self.write('source%i:power%i:mode %s'%(self.channel,port, mode))
    
    
        
    ## IO - Frequency related
    def get_f_start(self):
        '''
        Start frequency in Hz
        '''
        return float(self.ask('sens%i:FREQ:STAR?'%(self.channel)))
    
    def set_f_start(self,f):
        '''
        Start frequency in Hz
        '''
        self.write('sens%i:FREQ:STAR %f'%(self.channel,f))
    
    f_start = property(get_f_start, set_f_start)
        
    def get_f_stop(self):
        '''
        Stop frequency in Hz
        '''
        return float(self.ask('sens%i:FREQ:STOP?'%(self.channel)))
    
    def set_f_stop(self,f):
        '''
        Stop frequency in Hz
        '''
        self.write('sens%i:FREQ:STOP %f'%(self.channel,f))    
    
    f_stop = property(get_f_stop, set_f_stop)
    
    def get_f_npoints(self):
        '''
        Number of points for the measurment
        '''
        return int(self.ask('sens%i:swe:poin?'%(self.channel)))
    
    def set_f_npoints(self, n):
        '''
        Number of points for the measurment
        '''
        self.write('sens%i:swe:poin %i'%(self.channel,n))
    
    f_npoints = property(get_f_npoints, set_f_npoints)
    npoints = f_npoints        
    
    def get_frequency(self, unit='ghz'):
        '''
        Get frequency data for active meas.  
        
        This Returns a :class:`~skrf.frequency.Frequency` object.
        
        Parameters
        -------------
        unit : ['khz','mhz','ghz','thz']
            the frequency unit of the Frequency object.
        
        See Also
        ---------
        select_meas
        get_meas_list
        '''
        freq = Frequency(self.f_start,
                         self.f_stop,
                         self.f_npoints,'hz')
        freq.unit = unit
        
        return freq
    
    def set_frequency(self, freq):
        self.f_start = freq.start
        self.f_stop = freq.stop
        self.f_npoints = freq.npoints
    
    frequency = property(get_frequency,set_frequency)
    
    def get_frequency_cw(self):
        '''
        Sets the Continuous Wave (or Fixed) frequency. Must also send 
        SENS:SWEEP:TYPE CW to put the analyzer into CW sweep mode.
        
        Parameters
        --------------
        val : number
            CW frequency. Choose any number between the minimum and
            maximum frequency limits of the analyzer. Units are Hz.

        This command will accept MIN or MAX instead of a numeric 
        parameter. See SCPI Syntax for more information
        '''
        return float(self.ask('sens%i:FREQ?'%(self.channel)))
    
    def set_frequency_cw(self, val):
        self.write('sens%i:FREQ %f'%(self.channel,val)) 
    
    frequency_cw = property(get_frequency_cw, set_frequency_cw)
    
    ##  IO - S-parameter and  Networks
    def get_snp_format(self):
        '''
        the output format for snp data. 
        '''
        return self.ask('MMEM:STOR:TRAC:FORM:SNP?')
    
    def set_snp_format(self, val= 'ri'):
        '''
        the output format for snp data. 
        '''
        if val.lower() not in ['ma','ri','auto','disp']:
            raise ValueError('bad value for `val`')
        
        self.write('MMEM:STOR:TRAC:FORM:SNP %s'%val)
    
    snp_format = property(get_snp_format, set_snp_format)
    
    def get_network(self, sweep=True, name = None):
        '''
        Returns a :class:`~skrf.network.Network` object representing the 
        active trace.

        This can be used to get arbitrary traces, in the form of 
        Network objects, so that they can be plotted/saved/etc. 
         
        If you want to get s-parameter data, use :func:`get_twoport` or
        :func:`get_oneport`
        
        Parameters
        -----------
        sweep : Boolean
            trigger a sweep or not. see :func:`sweep`
        
        Examples
        ----------
        >>> from skrf.vi.vna import PNAX 
        >>> v = PNAX()
        >>> dut = v.get_network()
        
        See Also
        ----------
        get_network_all_meas
        '''
        
        was_cont = self.continuous
        self.continuous   = False
        if sweep:
            self.sweep()
            
        ntwk = Network(
            s = self.get_sdata(), 
            frequency = self.get_frequency(),
            )
        if name is None:
            name = self.get_active_meas()
        
        ntwk.name = name
        self.continuous = was_cont
        return ntwk
    
    def get_network_all_meas(self):
        '''
        Return list of Network Objects for all measurements.
        
        
        See Also
        -----------
        get_meas_list
        get_network
        '''
        
        out = []
        self.sweep()
        for name,parm in self.get_meas_list():
            self.select_meas(name)
            out.append(self.get_network(sweep=False, name= name))
        
        return out
            
    def get_oneport(self, port=1, *args, **kwargs):
        '''
        Get a one-port Network object for given ports.
        
        This calls :func:`~PNA.get_data_snp` and :func:`~PNA.get_frequency`
        to retrieve data, and then creates and returns a
        :class:`~skrf.network.Network` object.
        
        Parameters
        ------------
        ports : list of ints
            list of port indecies to retrieve data from
        
        \*args,\*\*kwargs : 
            passed to Network init
        
        See Also
        -----------
        get_twoport
        get_snp
        get_frequency
        '''
        was_cont = self.continuous
        self.continuous   = False
        self.sweep()
        ntwk = Network(
            s = self.get_data_snp(port), 
            frequency = self.get_frequency(),
            *args, **kwargs
            )
        self.continuous = was_cont
        return ntwk
        
    def get_twoport(self, ports=[1,2], *args, **kwargs):
        '''
        Get a two-port Network object for given ports.
        
        This calls :func:`~PNA.get_data_snp` and :func:`~PNA.get_frequency`
        to retrieve data, and then creates and returns a
        :class:`~skrf.network.Network` object.
        
        Parameters
        ------------
        ports : list of ints
            list of port indecies to retrieve data from
        
        \*args,\*\*kwargs : 
            passed to Network init
            
        '''
        was_cont = self.continuous
        self.continuous= False
        self.sweep()
        ntwk = Network(
            s = self.get_data_snp(ports), 
            frequency = self.get_frequency(),
            *args, **kwargs
            )
        self.continuous = was_cont
        return ntwk
    
    def get_data_snp(self,ports=[1,2]):
        '''
        Get n-port, s-parameter data.
        
        Returns s-parameter data of shape FXNXN where F is frequency 
        length and N is number of ports. This does not do any timing 
        see :func:`sweep` for that or use a higher level IO command, 
        which are listed below in `see also`.
        
        Note, this uses the  `calc:data:snp:ports` command
        
        Parameters
        ------------
        ports : list of ints
            list of port indecies to retrieve data from
        
        See Also
        ----------
        get_oneport
        get_twoport
        get_frequency
        '''
        
        if type(ports) == int:
            ports = [ports]
        
        
        d = self.ask_for_values('calc%i:data:snp:ports? \"%s\"'\
            %(self.channel,str(ports)[1:-1]))
        
        
        npoints = len(self.get_frequency())
        nports = len(ports)
        
        
        ##TODO: this could be re-written in a general matrical way so 
        # that testing for cases is not needed. i didnt have time.
        if nports==2:
            d = npy.array(d)
            d = d.reshape(9,-1).T
            s11 = d[:,1] +1j*d[:,2]
            s21 = d[:,3] +1j*d[:,4]
            s12 = d[:,5] +1j*d[:,6]
            s22 = d[:,7] +1j*d[:,8]
            s = npy.c_[s11,s12,s21,s22].reshape(-1,2,2)
        elif nports == 1:
            d = npy.array(d)
            d = d.reshape(3,-1).T
            s = (d[:,1] +1j*d[:,2]).reshape(-1,1,1)
        else:
            raise NotImplementedError()
        return s
    
    def get_data(self, char='SDATA', cnum = None):
        '''
        Get data for current active measuremnent
        
        Note that this doesnt do any sweep timing. It just gets whatever
        data is in the registers according to char.  If you want the 
        data to be returned after a sweep has completed 
        
        Parameters 
        ------------
        char : [SDATA, FDATA, RDATA]
            type of data to return 
            
            
        See Also
        ----------
        get_sdata
        get_fdata
        get_rdata
        get_snp_data
        
        '''
        if cnum is None:
            cnum = self.channel
            
        self.write('calc:par:sel \"%s\"'%(self.get_active_meas()))
        data = npy.array(self.ask_for_values('CALC%i:Data? %s'%(cnum, char)))
        
        if char.lower() == 'sdata':
            data = mf.scalar2Complex(data)
            
        return data
    
    def get_sdata(self, *args, **kwargs):
        '''
        Get complex data
        
        See Also
        ---------
        get_data
        
        '''
        out= self.get_data(char = 'SDATA', *args, **kwargs)
        
        return out
    
    def get_fdata(self, *args, **kwargs):
        '''
        Get formated data
        
        See Also
        ----------
        get_data
        '''
        return self.get_data(char = 'fDATA', *args, **kwargs)
    
    def get_rdata(self, char='A', cnum = None):
        '''
        Get data directly from the recievers.
        
        Parameters
        -----------
        char : ['A', 'B', 'C', ... , 'REF']
            the reciever to measure, the 'REF' number  (like R1, R2) 
            depends on the source port.
        cnum : int
            channel number
            
        '''
        if cnum is None:
            cnum = self.channel
        self.write('calc:par:sel %s'%(self.get_active_meas()))
        return npy.array(self.ask_for_values('CALC%i:RData? %s'%(cnum, char)))

    def get_switch_terms(self, ports = [1,2]):
        '''
        Get switch terms and return them as a tuple of Network objects. 
        
        Dont use this yet. 
        '''
        
        p1,p2 = ports
        self.delete_all_meas()
        self.create_meas('forward switch term', 'a%i/b%i,%i'%(p2,p2,p1))
        forward = self.get_network()
        
        
        self.delete_all_meas()
        self.create_meas('reverse switch term', 'a%i/b%i,%i'%(p1,p1,p2))
        reverse = self.get_network()
        self.delete_all_meas()
        return forward, reverse
    
    ## MEASUREMENT/TRACES
    @property
    def ntraces(self):
        '''
        The number of measurement traces that exist on the current channel
        
        Note that this may not be the same as the number of traces 
        displayed because a measurement may exist, but not be associated
        with a trace.
        
        '''
        n = self.get_meas_list()
        if n is None: 
            return 0
        else:
            return len(n)
    
    @property
    def if_bw(self):
        '''
        IF bandwidth
        '''
        return float(self.ask('sens%i:band?'%self.channel))
    
    @if_bw.setter
    def if_bw(self,n):
        '''
        IF bandwidth 
        '''
        self.write('sens%i:band %i'%(self.channel,n))
    

    def set_yscale_auto(self, window_n=None, trace_n=None):
        '''
        Display a given measurment on specified trace number. 
        
        Parameters
        ------------
        
        window_n : int
            window number. If None, active window is used.
        trace_n : int
            trace number to display on. If None, a new trace is made.
        '''
        if window_n is None:
            window_n =''
        if trace_n is None:
            trace_n =self.ntraces+1
        self.write('disp:wind%s:trac%s:y:scale:auto'%(str(window_n), str(trace_n))) 
        
    def get_meas_list(self):
        '''
        Get a list of existent measurements
        
        Returns
        ----------
        out :  list 
            list of tuples of the form, (name, measurement)
        '''
        meas_list = self.ask("CALC:PAR:CAT:EXT?")
        
        meas = meas_list[1:-1].split(',')
        if len(meas)==1:
            # if there isnt a single comma, then there arent any measurments
            return None
       
        
        return [(meas[k],meas[k+1]) for k in range(0,len(meas)-1,2)]
    
    def get_active_meas(self):
        '''
        Get the name of the active measurement
        '''
        out = self.ask("SYST:ACT:MEAS?")[1:-1]
        return out
    
    def delete_meas(self,name):
        '''
        Delete a measurement with name `name`
        
        
        '''
        self.write('calc%i:par:del %s'%(self.channel, name))
    
    def delete_all_meas(self):
        '''
        duh
        '''
        self.write('calc%i:par:del:all'%self.channel)
    
    def create_meas(self,name, meas):
        '''
        Create a new measurement. 
        
        Parameters 
        ------------
        name : str
            name given to measurment
        meas : str
            something like 
            * S11  
            * a1/b1,1 
            * A/R1,1
            * ...
        
        Examples
        ----------
        >>> p = PNA()
        >>> p.create_meas('my_meas', 'A/R1,1')     
        '''
        self.write('calc%i:par:def:ext \"%s\", \"%s\"'%(self.channel, name, meas))
        self.display_trace(name)
    
    def create_meas_hidden(self,name, meas):
        '''
        Create a new measurement but dont display it.
        
        Parameters 
        ------------
        name : str
            name given to measurment
        meas : str
            something like 
            * S11  
            * a1/b1,1 
            * A/R1,1
            * ...
        
        Examples
        ----------
        >>> p = PNA()
        >>> p.create_meas('my_meas', 'A/R1,1')     
        '''
        self.write('calc%i:par:def:ext %s, %s'%(self.channel, name, meas))
        
    def select_meas(self,name):
        '''
        Make a specified measurement active
        
        Parameters
        ------------
        name : str
            name of measurement. See :func:`get_meas_list`
        
        
        '''
        self.write('calc%i:par:sel \"%s\"'%(self.channel, name))

    def display_trace(self,  name = '',window_n = None, trace_n=None):
        '''
        Display a given measurment on specified trace number. 
        
        Parameters
        ------------
        name : str
            name of measurement. See :func:`get_meas_list`
        window_n : int
            window number. If None, active window is used.
        trace_n : int
            trace number to display on. If None, a new trace is made.
        '''
        if window_n is None:
            window_n =''
        if trace_n is None:
            trace_n =self.ntraces+1
        self.write('disp:wind%s:trac%s:feed \"%s\"'%(str(window_n), str(trace_n), name))    
    
    def set_display_format(self, form):
        '''
        Set the display format
        
        Choose from:
        
        * MLINear
        * MLOGarithmic
        * PHASe
        * UPHase 'Unwrapped phase
        * IMAGinary
        * REAL
        * POLar
        * SMITh
        * SADMittance 'Smith Admittance
        * SWR
        * GDELay 'Group Delay
        * KELVin
        * FAHRenheit
        * CELSius
        '''
        self.write('calc%i:form %s'%(self.channel,form))
        
    def set_display_format_all(self, form):
        '''
        Set the display format for all measurements
        
        Choose from:
        
        * MLINear
        * MLOGarithmic
        * PHASe
        * UPHase 'Unwrapped phase
        * IMAGinary
        * REAL
        * POLar
        * SMITh
        * SADMittance 'Smith Admittance
        * SWR
        * GDELay 'Group Delay
        * KELVin
        * FAHRenheit
        * CELSius

        '''
        self.func_on_all_traces(self.set_display_format, form)
    
    def func_on_all_traces(self,func, *args, **kwargs):
        '''
        Run a function on all traces are active
        
        Loop through all measurements, and making each active, then 
        subsequently run a command. 
        
        Parameters
        ------------
        func : func
            The function to run while each trace is active
            
        Examples
        ---------
        >>> p = PNA()
        >>> p.func_on_all_traces(p.set_display_format, 'smith')
        
        
        '''
        
        for name,parm in self.get_meas_list():
            self.select_meas(name)
            func(*args,**kwargs)
    
    def set_yscale_couple(self, method= 'all' ,window_n = None, trace_n=None):
        '''
        set y-scale coupling 
        
        Parameters
        ------------
        method : ['off','all','window']
            controls the coupling method
        '''
        if window_n is None:
            window_n =''
        if trace_n is None:
            trace_n =self.ntraces+1
        self.write('disp:wind%s:trac%s:y:coup:meth %s'%(str(window_n), str(trace_n), method))  
        
    def get_corr_state_of_channel(self):
        '''
        correction status for give channel
        '''
        return bool(int(self.ask('sense%i:corr:state?'%self.channel)))
    
    def set_corr_state_of_channel(self, val):
        '''
        toggle correction for give channel
        '''
        val = 'on' if val else 'off'
        self.write('sense%i:corr:state %s'%(self.channel, val))
    
    corr_state_of_channel = property(get_corr_state_of_channel,
        set_corr_state_of_channel)
    
    def get_corr_state_of_meas(self):
        '''
        correction status for give channel
        '''
        return bool(int(self.ask('calc%i:corr:state?'%self.channel)))
    
    def set_corr_state_of_meas(self, val):
        '''
        toggle correction for give channel
        '''
        val = 'on' if val else 'off'
        self.write('calc%i:corr:state %s'%(self.channel, val))
    
    corr_state_of_meas = property(get_corr_state_of_meas,
        set_corr_state_of_meas)
    
PNAX = PNA 
    
class ZVA40(PNA):
    def sweep(self):
        '''
        Initiates a sweep and waits for it to complete before returning
        
        If vna is in continuous sweep mode then this puts it back
        '''
        was_cont = self.continuous
        self.continuous = False
        self.write("INITiate%i:IMMediate;*WAI"%self.channel)
        self.ask('*OPC?;')
        self.continuous = was_cont
        
    def get_meas_list(self):
        '''
        Get a list of existent measurements
        
        Returns
        ----------
        out :  list 
            list of tuples of the form, (name, measurement)
        '''
        meas_list = self.ask("CALC:PAR:CAT?")
        
        meas = meas_list[1:-1].split(',')
        if len(meas)==1:
            # if there isnt a single comma, then there arent any measurments
            return None
       
        
        return [(meas[k],meas[k+1]) for k in range(0,len(meas)-1,2)]
    
    def get_data(self, char='SDATA', cnum = None):
        '''
        Get data for current active measuremnent
        
        Note that this doesnt do any sweep timing. It just gets whatever
        data is in the registers according to char.  If you want the 
        data to be returned after a sweep has completed 
        
        Parameters 
        ------------
        char : [SDATA, FDATA, RDATA]
            type of data to return 
            
            
        See Also
        ----------
        get_sdata
        get_fdata
        get_rdata
        get_snp_data
        
        '''
        if cnum is None:
            cnum = self.channel
            
        data = npy.array(self.ask_for_values('CALC%i:Data? %s'%(cnum, char)))
        
        if char.lower() == 'sdata':
            data = mf.scalar2Complex(data)
            
        return data
        
    def get_active_meas(self):
        '''
        Get the name of the active measurement
        '''
        warn('Retriving active trace is not functional. This is a stub.')
        
        return ''
    
    def create_meas(self,name, meas):
        '''
        Create a new measurement. 
        
        Parameters 
        ------------
        name : str
            name given to measurment
        meas : str
            something like 
            * S11  
            * a1/b1,1 
            * A/R1,1
            * ...
        
        Examples
        ----------
        >>> p = PNA()
        >>> p.create_meas('my_meas', 'A/R1,1')     
        '''
        self.write('calc%i:par:sdef \"%s\", \"%s\"'%(self.channel, name, meas))
        self.display_trace(name)
    
    def setup_twoport(self, ports=[1,2]):
        '''
        sets up traces appropriate for 2-port s-parameter measurment
        
        Parameters 
        -----------
        ports : tuple of ints
            the pair of ports on the VNA used in the measurement
        
        
        '''
        self.delete_all_meas()
        
        port_list = [(y,x) for x in ports for y in ports]
        #create traces
        for k in port_list:
            self.create_meas('s%i%i'%k,'s%i%i'%k)
    
    def get_twoport(self, *args, **kwargs):
        '''
        
        '''
        n = self.get_network_all_meas()
        twoport = n_oneports_2_nport([n[0],n[2],n[1],n[3]], *args, **kwargs)
        return twoport
    
    def setup_oneport(self, port=1):
        '''
        sets up traces appropriate for 1-port s-parameter measurment
        
        Parameters 
        -----------
        port : int
            the  port on the VNA used in the measurement
        
        '''
        self.setup_twoport(ports = [port])
    
    
    
    
    def set_source_freq_conversion(self, port, numer, denom, offset, mode='swe'):
        '''
        set source frequency for frequency converted measurments 
        
        fs = `numer`/`denom`*fb. + `offset`
        
        Parameters
        --------------
        numer : int
            numerator
        denom : int
            denominator
        offset : float 
            offset frequency in hz
        mode : ['swe','cw','fixed']
            sweep type
        '''
        self.write('SOUR%i:FREQ%i:CONV:ARB:IFR %i,%i,%f,%s'%\
            (self.channel, port, numer, denom, offset, mode))
    
    def set_source_power_permanent(self, port,val=True):
        '''
        set a given port to have its power permantly on 
        
        the same as having the 'gen' box checked in the `port config` 
        dialog
        
        Examples
        -----------
        >>>zva.set_source_power_permant(port =1, val= True)
        '''
        if val:
            val='on'
        else:
            val = 'off'
        self.write('source%i:power%i:perm %s'%(self.channel,port, val))
    
    def set_port_power_level(self, port, offset, only =True):
        '''
        Parameters
        -----------
        port : int
            port number
        offset : number 
            power offset (dB)
        only : bool
            if true: only set port power. ignore channel power.
            if false: the port power is added to channel ower. 
        '''
        
        if only:
            mode  = 'only'
        else:
            mode= 'cpad'
        self.write('source%i:power%i:offset %f, %s'\
            %(self.channel,port, offset, mode))
    
    
    
        
        
        
        
    get_oneport = PNA.get_network

class VectorStar(PNA):
    '''
    '''
    
    
    def rtl(self):
        '''
        Return to local 
        '''
        self.write('rtl')
    
    @property
    def continuous(self):
        out =  self.ask(':sense%i:hold:func?'%self.channel)
        if (out.lower() == 'hold' or out.lower() == 'sing'):
            return False
        else:
            return True
        

    @continuous.setter
    def continuous(self, mode):
        '''
        '''
        if mode:
            self.write(':sense%i:hold:func cont'%self.channel)
        else:
            self.write(':sense%i:hold:func hold'%self.channel)
    
    def sweep(self):
        '''
        Initiates a sweep and waits for it to complete before returning
        
        If vna is in continuous sweep mode then this puts it back
        '''
        was_cont = self.continuous
        self.continuous = False
        out = bool(self.ask("TRS;WFS;*IDN?"))
        self.continuous = was_cont
        return out
        
    def get_twoport(self, *args, **kwargs):
        '''
        Get a two-port Network using alternative command
        
        This method uses the `OS2P` command, which isnt documented,
        except for the examples, but its dang fast.
        
        
        
        '''
        self.write("LANG NATIVE")
        self.write(":FORM:SNP:FREQ HZ")
        self.write(":FORM:SNP:PAR REIM")
        d = self.ask_for_values("TRS;WFS;OS2P")[19:] # i dont know what the first 19 values are 
        d = npy.array(d)
        d = d.reshape(-1,9)
        s11 = d[:,1] +1j*d[:,2]
        s21 = d[:,3] +1j*d[:,4]
        s12 = d[:,5] +1j*d[:,6]
        s22 = d[:,7] +1j*d[:,8]
        s = npy.c_[s11,s12,s21,s22].reshape(-1,2,2)
        freq = self.frequency
        return Network(s = s, frequency = freq,*args, **kwargs)
    
    #def setup_wave_quantities(self):
        #self.ntraces = 4
        ##create traces
        #self.write(':calc%i:par1:def usr,a1,1,port1'%self.channel)
        #self.write(':calc%i:par2:def usr,b1,1,port1'%self.channel)
        #self.write(':calc%i:par3:def usr,a2,1,port2'%self.channel)
        #self.write(':calc%i:par4:def usr,b2,1,port2'%self.channel)
        ## set display to log mag
        #for k in range(1,5):
        #    self.write('calc%i:par%i:form mlog'%(self.channel,k))
    
    def setup_s_parameters(self):
        self.ntraces = 4
        #create traces
        self.write(':calc%i:par1:def s11'%self.channel)
        self.write(':calc%i:par2:def s12'%self.channel)
        self.write(':calc%i:par3:def s21'%self.channel)
        self.write(':calc%i:par4:def s22'%self.channel)
        # set display to log mag
        for k in range(1,5):
            self.write(':calc%i:par%i:form mlog'%(self.channel,k))
    
    def get_wave_quantities(self):
        self.ntraces = 4
        #create traces
        self.write(':calc%i:par1:def usr, a1,1,port1'%self.channel)
        self.write(':calc%i:par2:def usr, b1,1,port1'%self.channel)
        self.write(':calc%i:par3:def usr, a2,1,port2'%self.channel)
        self.write(':calc%i:par4:def usr, b2,1,port2'%self.channel)
        
        self.active_trace = 1
        a1 = self.get_oneport(name = 'a1')
        self.active_trace = 2
        b1 = self.get_oneport(name = 'b1')
        self.active_trace = 3
        a2 = self.get_oneport(name = 'a2')
        self.active_trace = 4
        b2 = self.get_oneport(name = 'b2')
        return a1,b1,a2,b2
    
    def get_oneport(self, n=None, *args, **kwargs):
        was_cont = self.continuous
        self.continuous = False
        
        if n is not None:
            self.active_trace = n
        freq = self.frequency
        s = npy.array(self.get_sdata())
        s = mf.scalar2Complex(s)
        
        self.continuous = was_cont
        return Network(
            frequency = freq, 
            s=s,
            *args, 
            **kwargs)    
    
    def get_twoport_slow(self, *args, **kwargs):
        was_cont = self.continuous
        self.continuous = False
        self.setup_s_parameters()
        self.active_trace = 1
        s11 = mf.scalar2Complex(self.get_sdata())
        self.active_trace = 3
        s21 = mf.scalar2Complex(self.get_sdata())
        self.active_trace = 2
        s12 = mf.scalar2Complex(self.get_sdata())
        self.active_trace = 4
        s22 = mf.scalar2Complex(self.get_sdata())
        
        s = npy.c_[s11,s12,s21,s22].reshape(-1,2,2)
        freq = self.frequency
        self.continuous=was_cont    
        return Network(s = s, frequency = freq,*args, **kwargs)
    
    def get_network_all_meas(self):
        '''
        Return list of Network Objects for all measurements.
        
        
        See Also
        -----------
        get_meas_list
        get_network
        '''
        
        out = []
        self.sweep()
        for name,parm in self.get_meas_list():
            self.select_meas(name)
            out.append(self.get_network(sweep=False, name= parm))
        
        return out    
    
    def get_ntraces(self):
        return int(self.ask(':calc%i:par:count?'%self.channel))
    
    def set_ntraces(self,val):
        self.write((':calc%i:par:count %i'%(self.channel,int(val))))
    
    ntraces = property(get_ntraces, set_ntraces)
    
    def get_active_meas(self):
        '''
        Get the name of the active measurement
        '''
        return self.ask(':calc%i:par%i:def?'%(self.channel, self.active_trace_num))
    
    def create_meas(self,name, meas):
        '''
        Create a new measurement. 
        
        Parameters 
        ------------
        name : str
            name given to measurment
        meas : str
            something like 
            * S11  
            * a1/b1,1 
            * A/R1,1
            * ...
        
        Examples
        ----------
        >>> p = PNA()
        >>> p.create_meas('my_meas', 'A/R1,1')     
        '''
        # translate agilent's semantics into Anritu's 
        # TODO: use regex to fully translate all combos
        translation_dict  = {
                             '/':',',
                             'R1':'A1',
                             'R2':'A2',
                             'R3':'A3',
                             'R4':'A4',
                             }
                             
        if meas.lower().startswith('s'):
            # measuring an s-parameter, es simple.
            self.write('calc%i:par%i:def %s'%(self.channel,(self.ntraces+1), meas))                  
        else:
            # measuring something other than s-parameters, need to do 
            # some translation .. . 
            meas, port = meas.split(',')
            for k in translation_dict:
                meas = meas.replace(k,translation_dict[k]) 
        
            self.write('calc%i:par%i:def:usr %s,%s,port%s'%(self.channel,
                                                            self.ntraces+1, 
                                                            meas, port))
        
    def get_active_trace_num(self):
        return int(self.ask(':calc%i:par:sel?'%self.channel))
    
    
    def set_active_trace_num(self,n):
        n = int(n)
        self.write(':calc%i:par%i:sel'%(self.channel, n))
    
    active_trace_num = property(get_active_trace_num,set_active_trace_num)
    
    select_meas = set_active_trace_num
    
    @property
    def trace_format(self):
        return self.ask('calc%i:form?'%self.channel)
        
    @trace_format.setter
    def trace_format(self, form):
        self.write(':calc%i:form %s'%(self.channel, form))
    
    
    
    def get_fdata(self):
        return npy.array(self.ask_for_values('trs;wfs;:calc%i:data:fdat?'%self.channel))[1:]
            
    def get_sdata(self):
        return npy.array(self.ask_for_values('trs;wfs;:calc%i:data:sdat?'%self.channel))[1:]
    
    def get_smem(self):
        return npy.array(self.ask_for_values('trs;wfs;:calc%i:data:smem?'%self.channel))[1:]
    
    def delete_all_meas(self):
        self.ntraces = 0 
    
    
     
    def get_all_traces(self):
        ntwks = []
        for k in  range(1, self.ntraces+1):
            self.active_trace_num =k
            ntwks.append(self.get_oneport(name = self.get_active_meas()))
    
        return ntwks
    
    def get_meas_list(self):
        '''
        Get a list of existent measurements
        
        Returns
        ----------
        out :  list 
            list of tuples of the form, (name, measurement)
        '''
        meas_list = []
        for k in  range(1, self.ntraces+1):
            self.active_trace_num =k
            meas_list.append(self.get_active_meas())
        
       
        
        return [(k+1,meas_list[k]) for k in range(self.ntraces)]
        
class ZVA40_lihan(object):
    '''
    Created on Aug 3, 2010
    @author: Lihan

    This class is create to remote control Rohde & Schwarz by using pyvisa.
    For detail about visa please refer to:
            http://pyvisa.sourceforge.net/

    After installing the pyvisa and necessary driver (GPIB to USB driver,
     for instance), please follow the pyvisa manual to set up the module

    This class only has several methods. You can add as many methods
    as possible by reading the Network Analyzer manual
    Here is an example

    In the manual,

            "CALC:DATA? FDAT"

    This is the SCPI command

            "Query the response values of the created trace. In the FDATa setting, N
            comma-separated ASCII values are returned."

    This descripes the function of the SCPI command above

    Since this command returns ASCII values, so we can use ask_for_values method in pyvisa

    temp=vna.ask_for_values('CALCulate1:DATA? SDATa')

    vna is a pyvisa.instrument instance


    '''
    def __init__(self,address=20, **kwargs):
        self.vna=visa.instrument('GPIB::'+str(address),**kwargs)
        self.spara=npy.array([],dtype=complex)

    def continuousOFF(self):
        self.vna.write('initiate:continuous OFF')


    def continuousON(self):
        self.vna.write('initiate:continuous ON')

    def displayON(self):
        self.vna.write('system:display:update ON')

    def setFreqBand(self,StartFreq,StopFreq):
        '''
        Set the frequency band in GHz
        setFreqBand(500,750)
        Start frequency 500GHz, Stop frequency 750GHz
        '''
        self.freqGHz=npy.linspace(StartFreq, StopFreq, 401)
        self.vna.write('FREQ:STAR '+'StartFreq'+'GHz')
        self.vna.write('FREQ:STOP '+'StopFreq'+'GHz')

    def sweep(self):
        '''
        Initiate a sweep under continuous OFF mode
        '''
        self.vna.write('initiate;*WAI')

    def getData(self):
        '''
        Get data from current trace
        '''
        temp=self.vna.ask_for_values('CALCulate1:DATA? SDATa')
        temp=npy.array(temp)
        temp.shape=(-1,2)
        self.spara=temp[:,0]+1j*temp[:,1]
        self.spara.shape=(-1,1,1)                       #this array shape is compatible to Network Class
        return self.spara

    def measure(self):
        '''
        Take one-port measurement
        1.turn continuous mode off
        2.initiate a single sweep
        3.get the measurement data
        4.turn continuous mode on
        '''
        self.continuousOFF()
        self.sweep()
        temp=self.getData()
        self.continuousON()
        return temp

    def saveSpara(self,fileName):
        '''
        Take one-port measurement and save the data as touchstone file, .s1p
        '''
        temp=self.spara
        formatedData=npy.array([self.freqGHz[:],temp[:,0,0].real,temp[:,0,0].imag],dtype=float)
        fid = open(fileName+'.s1p', 'w')
        fid.write("# GHz S RI R 50\n")
        npy.savetxt(fid,formatedData,fmt='%10.5f')
        fid.close()

class ZVA40_old(GpibInstrument):
    '''
    Rohde&Scharz ZVA40
    
    Examples
    -----------
    
    >>> from skrf.vi.vna import ZVA40 
    >>> v = ZVA40()
    >>> dut = v.network
    '''
    def __init__(self, address=20, active_channel = 1, continuous=True,\
            **kwargs):
        GpibInstrument.__init__(self,address, **kwargs)
        self.active_channel = active_channel
        self.continuous = continuous
        self.traces = []
        #self.update_trace_list()

    @property
    def sdata(self):
        '''
        unformated s-parameter data [a numpy array]
        '''
        return npy.array(self.ask_for_values(\
                'CALCulate%i:DATA? SDATa'%(self.active_channel)))

    @property
    def fdata(self):
        '''
        formated s-parameter data [a numpy array]
        '''
        return npy.array(self.ask_for_values(\
                'CALCulate%i:DATA? FDATa'%(self.active_channel)))

    @property
    def continuous(self):
        '''
        set/get continuous sweep mode on/off [boolean]
        '''
        return self._continuous

    @continuous.setter
    def continuous(self, value):
        if value:
            self.write('INIT%i:CONT ON;'%(self.active_channel))
            self._continuous = True
        elif not value:
            self.write('INIT%i:CONT OFF;'%(self.active_channel))
            self._continuous = False
        else:
            raise ValueError('takes boolean')


    @property
    def frequency(self, unit='ghz'):
        '''
        a frequency object, representing the current frequency axis
        [skrf Frequency object]
        '''
        freq=Frequency(0,0,0)
        freq.f = self.ask_for_values(\
                'CALC%i:DATA:STIMulus?'%self.active_channel)
        freq.unit = unit
        return freq

    @property
    def one_port(self):
        '''
        a network representing the current active trace
        [skrf Network object]
        '''
        self.sweep()
        s = self.sdata
        s.shape=(-1,2)
        s =  s[:,0]+1j*s[:,1]
        ntwk = Network()
        ntwk.s = s
        ntwk.frequency= self.frequency
        return ntwk

    @property
    def s11(self):
        '''
        this is just for legacy support, there is no gurantee this
        will return s11. it just returns active trace
        '''
        return self.one_port

    @property
    def error(self):
        '''
        returns list errors stored on vna
        '''
        return self.ask('OUTPERROR?')

    def initiate(self):
        '''
        initiate a sweep on current channel (low level timing)
        '''
        self.write('INITiate%i'%self.active_channel)

    def sweep(self):
        '''
        initiate a sweep on current channel. if vna is in continous
        mode it will put in single sweep mode, then request a sweep,
        and then return sweep mode to continous.
        '''
        if self.continuous:
            self.continuous = False
            self.write(\
                    'INITiate%i:IMMediate;*WAI'%self.active_channel)
            self.continuous = True
        else:
            self.write(\
                    'INITiate%i:IMMediate;*WAI'%self.active_channel)

    def wait(self):
        '''
        wait for preceding command to finish before executing subsequent
        commands
        '''
        self.write('*WAIt')

    def add_trace(self, parameter, name):
        print ('CALC%i:PARA:SDEF \"%s\",\"%s\"'\
                %(self.active_channel, name, parameter))
        self.write('CALC%i:PARA:SDEF \"%s\",\"%s\"'\
                %(self.active_channel, name, parameter))
        self.traces[name] = parameter

    def set_active_trace(self, name):
        if name in self.traces:
            self.write('CALC%i:PAR:SEL %s'%(self.active_channel,name))
        else:
            raise ValueError('trace name does exist')
    def update_trace_list(self):
        raise(NotImplementedError)

    def upload_cal_data(self, error_data, cal_name='test', port=1):
        '''
        for explanation of this code see the 
        zva manual (v1145.1084.12 p6.193)
        '''
        directivity  = error_data.s[:,0,0]
        source_match  = error_data.s[:,1,1]
        reflection_tracking  = error_data.s[:,1,0]*error_data.s[:,0,1]
        
        def flatten_to_string(z):
            return ''.join(['%s,'%k for k in mf.complex2Scalar(z)])
        
        error_dict={}
        if port ==1:
            error_dict['DIRECTIVITY'] = flatten_to_string(directivity)[0:-2]
            error_dict['SRCMATCH'] = flatten_to_string(source_match)[0:-2]
            error_dict['REFLTRACK'] = flatten_to_string(reflection_tracking)[0:-2]
        
        cal_type = 'FOPort'%port
        self.write('CORR:COLL:METH:DEF \'%s\', %s, %i'%(cal_name, cal_type,port))
        self.write('corr:coll:save:sel:def')
        self.continuous=False
        for key in error_dict:
            self.write('corr:dat \'%s\',%i,0,%s'\
            %(key, port, error_dict[key]))
    
        self.continuous=True
    
    def get_port_config(self):
        raise NotImplementedError
    
    
        
    def set_port_config(self, ch=1, pt=1, num=1, denom=1, offset=0, 
                        sweep_type='sweep'):
        '''
        Parameters
        -----------
        ch : int 
            channel number
        pt : int
            port number
        num : int
            numerator 
        denom : int
            denominator
        offset : float 
            offset frequency [hz]
        sweep_type: ['sweep','cw','fixed']
            sweep type. 
    
        '''
        gpib_str = 'SOUR{ch}:FREQ:{pt}:CONV:ARB:IFR {num}, {denom}, {offset}, {sweep_type}'.format(ch = ch, pt = pt, num = num, denom = denom, 
                      offset = offset, sweep_type = sweep_type)
        self.write(gpib_str)
        
        
class ZVA40_alex(GpibInstrument):
    '''
    the rohde Swarz zva40
    '''
    class Channel(object):
        def __init__(self, vna, channel_number):
            self.number = channel_number
            self.vna = vna
            self.traces = {}
            self.continuous = True

        @property
        def sdata(self):
            return npy.array(self.vna.ask_for_values('CALCulate%i:DATA? SDATa'%(self.number)))
        @property
        def fdata(self):
            return npy.array(self.vna.ask_for_values('CALCulate%i:DATA? FDATa'%(self.number)))
        @property
        def continuous(self):
            return self._continuous
        @continuous.setter
        def continuous(self, value):
            if value:
                self.vna.write('INIT%i:CONT ON;'%(self.number))
                self._continuous = True
            elif not value:
                self.vna.write('INIT%i:CONT OFF;'%(self.number))
                self._continuous = False
            else:
                raise ValueError('takes boolean')

        def initiate(self):
            self.vna.write('INITiate%i'%self.number)

        def sweep(self):
            if self.continuous:
                self.continuous = False
                self.vna.write('INITiate%i:IMMediate;*WAI'%self.number)
                self.continuous = True
            else:
                self.vna.write('INITiate%i:IMMediate;*WAI'%self.number)

        def add_trace(self, parameter, name):
            print ('CALC%i:PARA:SDEF \"%s\",\"%s\"'\
                    %(self.number, name, parameter))
            self.vna.write('CALC%i:PARA:SDEF \"%s\",\"%s\"'\
                    %(self.number, name, parameter))
            self.traces[name] = parameter

        def select_trace(self, name):
            if name in self.traces.keys():
                self.vna.write('CALC%i:PAR:SEL %s'%(self.number,name))
            else:
                raise ValueError('trace name does exist')

        @property
        def frequency(self, unit='ghz'):
            freq=Frequency(0,0,0)
            freq.f = self.vna.ask_for_values('CALC%i:DATA:STIMulus?'%self.number)
            freq.unit = unit
            return freq
        @property
        def one_port(self):
            self.sweep()
            s = self.sdata
            s.shape=(-1,2)
            s =  s[:,0]+1j*s[:,1]
            ntwk = Network()
            ntwk.s = s
            ntwk.frequency= self.frequency
            return ntwk

    def __init__(self, address=20,**kwargs):
        GpibInstrument.__init__(self,address, **kwargs)
        self.add_channel(1)

    def _set_property(self, name, value):
        setattr(self, '_' + name, value)
    def _get_property(self, name):
        return getattr(self, '_' + name)

    @property
    def error(self):
        return self.ask('OUTPERROR?')
    def add_channel(self,channel_number):
        channel = self.Channel(self, channel_number)
        fget = lambda self: self._get_property('ch'+str(channel_number))
        setattr(self.__class__,'ch'+str(channel_number), property(fget))
        setattr(self, '_'+'ch'+str(channel_number), channel)



    def wait(self):
        self.write('*WAIt')

class HP8510C(GpibInstrument):
    '''
    good ole 8510
    '''
    def __init__(self, address=16,**kwargs):
        GpibInstrument.__init__(self,'GPIB::'+str(address),**kwargs)
        self.write('FORM4;')



    @property
    def error(self):
        return self.ask('OUTPERRO')
    @property
    def continuous(self):
        answer_dict={'\"HOLD\"':False,'\"CONTINUAL\"':True}
        return answer_dict[self.ask('GROU?')]

    @continuous.setter
    def continuous(self, choice):
        if choice:
            self.write('CONT;')
        elif not choice:
            self.write('SING;')
        else:
            raise(ValueError('takes a boolean'))
    @property
    def averaging(self):
        '''
        averaging factor
        '''
        raise NotImplementedError

    @averaging.setter
    def averaging(self, factor ):
        self.write('AVERON %i;'%factor )

    @property
    def frequency(self, unit='ghz'):
        freq=Frequency( float(self.ask('star;outpacti;')),
                float(self.ask('stop;outpacti;')),\
                int(float(self.ask('poin;outpacti;'))),'hz')
        freq.unit = unit
        return freq


    @property
    def one_port(self):
        '''
        Initiates a sweep and returns a  Network type represting the
        data.

        if you are taking multiple sweeps, and want the sweep timing to
        work, put the turn continuous mode off. like pnax.continuous='off'
        '''
        #tmp_continuous = self.continuous
        #if self.continuous:
        #       tmp_continuous =True
        self.continuous = False
        s = npy.array(self.ask_for_values('OUTPDATA'))
        s.shape=(-1,2)
        s =  s[:,0]+1j*s[:,1]
        ntwk = Network()
        ntwk.s = s
        ntwk.frequency= self.frequency
        #self.continuous  = tmp_continuous
        return ntwk

    @property
    def two_port(self):
        '''
        Initiates a sweep and returns a  Network type represting the
        data.

        if you are taking multiple sweeps, and want the sweep timing to
        work, put the turn continuous mode off. like pnax.continuous='off'
        '''
        print ('s11')
        s11 = self.s11.s[:,0,0]
        print ('s12')
        s12 = self.s12.s[:,0,0]
        print ('s22')
        s22 = self.s22.s[:,0,0]
        print ('s21')
        s21 = self.s21.s[:,0,0]

        ntwk = Network()
        ntwk.s = npy.array(\
                [[s11,s21],\
                [ s12, s22]]\
                ).transpose().reshape(-1,2,2)
        ntwk.frequency= self.frequency

        return ntwk
    ##properties for the super lazy
    @property
    def s11(self):
        self.write('s11;')
        ntwk =  self.one_port
        ntwk.name = 'S11'
        return ntwk
    @property
    def s22(self):
        self.write('s22;')
        ntwk =  self.one_port
        ntwk.name = 'S22'
        return ntwk
    @property
    def s12(self):
        self.write('s12;')
        ntwk =  self.one_port
        ntwk.name = 'S12'
        return ntwk
    @property
    def s21(self):
        self.write('s21;')
        ntwk =  self.one_port
        ntwk.name = 'S21'
        return ntwk

    @property
    def switch_terms(self):
        '''
        measures forward and reverse switch terms and returns them as a
        pair of one-port networks.

        returns:
                forward, reverse: a tuple of one ports holding forward and
                        reverse switch terms.

        see also:
                skrf.calibrationAlgorithms.unterminate_switch_terms

        notes:
                thanks to dylan williams for making me aware of this, and
                providing the gpib commands in his statistical help

        '''
        print('forward')
        self.write('USER2;DRIVPORT1;LOCKA1;NUMEB2;DENOA2;CONV1S;')
        forward = self.one_port
        forward.name = 'forward switch term'

        print ('reverse')
        self.write('USER1;DRIVPORT2;LOCKA2;NUMEB1;DENOA1;CONV1S;')
        reverse = self.one_port
        reverse.name = 'reverse switch term'

        return (forward,reverse)

PNAX = PNA

class HP8720(HP8510C):
    def __init__(self, address=16,**kwargs):
        HP8510C.__init__(self,address,**kwargs)
    @property
    def averaging(self):
        raise ( NotImplementedError)
    @averaging.setter
    def averaging(self,value):
        if value:
            self.write('AVEROON')
        else:
            self.write('AVEROFF')
    @property
    def ifbw(self):
        raise ( NotImplementedError)
    
    @ifbw.setter
    def ifbw(self,value):
        self.write('IFBW %i'%int(value))

    @property
    def frequency(self, unit='ghz'):
        f = npy.array(self.ask_for_values('OUTPLIML'))
        f.shape=(-1,4)
        freq=Frequency.from_f(f[:,0], unit='hz')
        freq.unit = unit
        return freq
